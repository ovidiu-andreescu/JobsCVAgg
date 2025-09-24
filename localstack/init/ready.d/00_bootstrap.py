#!/usr/bin/env python3
# LocalStack bootstrapper: reads /etc/localstack/init/manifest.json and provisions:
# - S3 buckets
# - DynamoDB tables (+ GSIs)
# - Lambda functions (zips built from your source tree)
# - S3 -> Lambda notifications (with proper permission & filter)
# - EventBridge schedules
# - API Gateway REST proxy for FastAPI/Mangum (if configured)

import os, sys, json, time, zipfile, shutil, pathlib, subprocess, re
from io import BytesIO
from botocore.exceptions import ClientError
import boto3

# -------------------------------------------------------------------
# Environment & defaults
# -------------------------------------------------------------------
# Dummy creds for boto3 in LocalStack
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

EDGE = os.environ.get("LOCALSTACK_EDGE_URL", "http://localhost:4566")

def find_manifest() -> str:
    for cand in (
        "/etc/localstack/init/manifest.json",
        "/etc/localstack/init/ready.d/../manifest.json",
        "/workspace/localstack/manifest.json",
    ):
        if os.path.isfile(cand):
            return cand
    return ""

MANIFEST_PATH = find_manifest()
if not MANIFEST_PATH:
    print("ERROR: manifest.json not found in expected locations.", file=sys.stderr)
    sys.exit(1)

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

REGION = manifest.get("region", os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"))
os.environ["AWS_DEFAULT_REGION"] = REGION

print(f"==> LocalStack bootstrap (region: {REGION}) using MANIFEST={MANIFEST_PATH}")

# -------------------------------------------------------------------
# Clients
# -------------------------------------------------------------------
session = boto3.session.Session(region_name=REGION)
s3      = session.client("s3",        endpoint_url=EDGE)
ddb     = session.client("dynamodb",  endpoint_url=EDGE)
lam     = session.client("lambda",    endpoint_url=EDGE)
logs    = session.client("logs",      endpoint_url=EDGE)
events  = session.client("events",    endpoint_url=EDGE)
apigw   = session.client("apigateway",endpoint_url=EDGE)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def ensure_log_group(name: str):
    try:
        logs.create_log_group(logGroupName=name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
            raise

def create_bucket(name: str):
    try:
        s3.create_bucket(
            Bucket=name,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise

def create_table(tbl: dict):
    name = tbl["name"]
    hash_name = tbl["hashKey"]["name"]
    hash_type = tbl["hashKey"]["type"]

    # Build attribute definitions (dedupe)
    attrs = {(hash_name, hash_type)}
    for a in tbl.get("attributes", []):
        attrs.add((a["name"], a["type"]))

    # Include GSI keys in attribute defs
    for g in tbl.get("globalSecondaryIndexes", []):
        attrs.add((g["hashKey"]["name"], g["hashKey"]["type"]))

    attr_defs = [{"AttributeName": k, "AttributeType": t} for (k, t) in attrs]

    params = {
        "TableName": name,
        "AttributeDefinitions": attr_defs,
        "KeySchema": [{"AttributeName": hash_name, "KeyType": "HASH"}],
        "BillingMode": tbl.get("billingMode", "PAY_PER_REQUEST"),
    }

    gsis = tbl.get("globalSecondaryIndexes", [])
    if gsis:
        params["GlobalSecondaryIndexes"] = []
        for g in gsis:
            params["GlobalSecondaryIndexes"].append({
                "IndexName": g["name"],
                "KeySchema": [{"AttributeName": g["hashKey"]["name"], "KeyType": "HASH"}],
                "Projection": {"ProjectionType": g.get("projection", "ALL")},
            })

    try:
        ddb.create_table(**params)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise

    # Wait ACTIVE
    for _ in range(50):
        d = ddb.describe_table(TableName=name)
        if d["Table"]["TableStatus"] == "ACTIVE":
            break
        time.sleep(0.2)

def rsync_tree(src: pathlib.Path, dst: pathlib.Path):
    if not src.exists():
        return
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        q = dst / rel
        if p.is_dir():
            q.mkdir(parents=True, exist_ok=True)
        else:
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(p.read_bytes())

def add_init_py(root: pathlib.Path):
    for d, _, _ in os.walk(root):
        p = pathlib.Path(d) / "__init__.py"
        if not p.exists():
            p.write_text("", encoding="utf-8")

def pip_install(requirements_path: pathlib.Path, target_dir: pathlib.Path):
    if not requirements_path.exists():
        return
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-q",
         "-t", str(target_dir), "-r", str(requirements_path)]
    )

def build_lambda_zip(name: str, src_root: str, pkg_root: str,
                     copy_mode: str, with_libs_common: bool,
                     pip_requirements: str) -> pathlib.Path:
    outdir = pathlib.Path(f"/tmp/build/{name}")
    if outdir.exists():
        shutil.rmtree(outdir)
    pkg_dir = outdir / pkg_root
    pkg_dir.mkdir(parents=True, exist_ok=True)

    ws_src = pathlib.Path("/workspace") / src_root

    # Copy sources (we default to "all")
    if copy_mode == "all":
        rsync_tree(ws_src, pkg_dir)
    else:
        # If you ever add a file-list mode, implement here
        rsync_tree(ws_src, pkg_dir)

    # Ensure packages
    add_init_py(pkg_dir)

    # libs/common (shared) if requested
    if with_libs_common:
        libs_src = pathlib.Path("/workspace/libs/common/src")
        libs_dst = outdir / "libs" / "common" / "src"
        rsync_tree(libs_src, libs_dst)
        add_init_py(outdir / "libs")
        add_init_py(outdir / "libs/common")
        add_init_py(libs_dst)

    # Optional per-service deps
    if pip_requirements:
        req_path = pathlib.Path("/workspace") / src_root / pip_requirements
        if req_path.exists():
            pip_install(req_path, outdir)

    # Zip
    zip_path = pathlib.Path(f"/tmp/build/{name}.zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in outdir.rglob("*"):
            zf.write(p, p.relative_to(outdir))
    return zip_path

def deploy_lambda(fn: dict):
    name    = fn["name"]
    runtime = fn.get("runtime", "python3.11")
    handler = fn["handler"]
    memory  = fn.get("memory", 512)
    timeout = fn.get("timeout", 60)
    pkg     = fn["package"]

    zip_path = build_lambda_zip(
        name=name,
        src_root=pkg["source_root"],
        pkg_root=pkg["package_root"],
        copy_mode=pkg.get("copy_mode", "all"),
        with_libs_common=pkg.get("with_libs_common", False),
        pip_requirements=pkg.get("pip_requirements", ""),
    )

    # Recreate function (idempotent)
    try:
        lam.delete_function(FunctionName=name)
    except ClientError:
        pass

    env_vars = fn.get("env", {})
    with open(zip_path, "rb") as f:
        code_bytes = f.read()

    lam.create_function(
        FunctionName=name,
        Runtime=runtime,
        Role="arn:aws:iam::000000000000:role/lambda-exec-role",
        Handler=handler,
        Code={"ZipFile": code_bytes},
        Timeout=timeout,
        MemorySize=memory,
        Environment={"Variables": env_vars} if env_vars else {},
        Publish=True,
    )

def get_account_id_from_arn(arn: str) -> str:
    # arn:aws:lambda:<region>:<acct>:function:<name>
    m = re.match(r"arn:aws:[^:]+:[^:]+:(\d{12}):", arn)
    return m.group(1) if m else "000000000000"

def allow_s3_invoke(function_arn: str, bucket: str):
    """
    Add resource-based policy so S3 can invoke the Lambda.
    Use Function ARN + SourceArn + SourceAccount. Idempotent.
    """
    try:
        lam.add_permission(
            FunctionName=function_arn,  # ARN form
            StatementId=f"allow-s3-{bucket}",
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn=f"arn:aws:s3:::{bucket}",
            SourceAccount=get_account_id_from_arn(function_arn),
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise

def wire_s3_notify(bucket: str, function_arn: str, prefix: str = None, suffix: str = None):
    """
    PutBucketNotificationConfiguration with correct Filter shape ("Key"),
    after permission is in place. Retries once for eventual consistency.
    """
    rules = []
    if isinstance(prefix, str) and prefix.strip():
        rules.append({"Name": "prefix", "Value": prefix})
    if isinstance(suffix, str) and suffix.strip():
        rules.append({"Name": "suffix", "Value": suffix})

    cfg = {
        "LambdaFunctionConfigurations": [
            {
                "Id": "cv-upload-created",
                "LambdaFunctionArn": str(function_arn),
                "Events": ["s3:ObjectCreated:*"],
            }
        ]
    }
    if rules:
        cfg["LambdaFunctionConfigurations"][0]["Filter"] = {"Key": {"FilterRules": rules}}

    # small delay so permission is visible
    time.sleep(0.3)
    try:
        s3.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=cfg)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("InvalidArgument", "MalformedXML"):
            time.sleep(0.7)
            s3.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=cfg)
        else:
            raise

def schedule_rule(rule_name: str, schedule: str, target_arn: str):
    events.put_rule(Name=rule_name, ScheduleExpression=schedule, State="ENABLED")
    events.put_targets(Rule=rule_name, Targets=[{"Id": "1", "Arn": target_arn}])

def create_rest_api_proxy(api_name: str, stage: str, lambda_arn: str) -> str:
    api_id = apigw.create_rest_api(name=api_name)["id"]
    resources = apigw.get_resources(restApiId=api_id)
    root_id = [r for r in resources["items"] if r.get("path") == "/"][0]["id"]
    # /{proxy+}
    res_id = apigw.create_resource(restApiId=api_id, parentId=root_id, pathPart="{proxy+}")["id"]
    for rid in (root_id, res_id):
        apigw.put_method(restApiId=api_id, resourceId=rid, httpMethod="ANY", authorizationType="NONE")
        apigw.put_integration(
            restApiId=api_id, resourceId=rid, httpMethod="ANY",
            type="AWS_PROXY", integrationHttpMethod="POST",
            uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
        )
    # permission for apigw to invoke lambda
    try:
        lam.add_permission(
            FunctionName=lambda_arn.split(":")[-1],
            StatementId=f"apigw-invoke-{int(time.time())}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
        )
    except ClientError:
        pass
    apigw.create_deployment(restApiId=api_id, stageName=stage)
    return api_id

# -------------------------------------------------------------------
# Provisioning
# -------------------------------------------------------------------
# Buckets
for b in manifest.get("buckets", []):
    name = b["name"]
    print(f" -> bucket: {name}")
    create_bucket(name)

# DynamoDB
for t in manifest.get("dynamodb", {}).get("tables", []):
    print(f" -> table: {t['name']}")
    create_table(t)

# Lambdas (+triggers/schedules/APIGW)
for L in manifest.get("lambdas", []):
    name = L["name"]
    print(f" -> lambda: {name}")
    deploy_lambda(L)

    # S3 triggers (exact order: grant permission -> configure bucket)
    s3_trigs = L.get("triggers", {}).get("s3", []) or []
    if s3_trigs:
        fn_arn = lam.get_function(FunctionName=name)["Configuration"]["FunctionArn"]
        for trig in s3_trigs:
            bucket = trig["bucket"]
            prefix = trig.get("filter_prefix")
            suffix = trig.get("filter_suffix")
            allow_s3_invoke(fn_arn, bucket)
            wire_s3_notify(bucket=bucket, function_arn=fn_arn, prefix=prefix, suffix=suffix)

    # EventBridge schedules
    evt_trigs = L.get("triggers", {}).get("events", []) or []
    if evt_trigs:
        fn_arn = lam.get_function(FunctionName=name)["Configuration"]["FunctionArn"]
        for e in evt_trigs:
            schedule_rule(f"{name}-schedule", e["schedule"], fn_arn)

    # API Gateway
    if "apigateway" in L:
        fn_arn = lam.get_function(FunctionName=name)["Configuration"]["FunctionArn"]
        api_id = create_rest_api_proxy(
            api_name=L["apigateway"]["name"],
            stage=L["apigateway"]["stage"],
            lambda_arn=fn_arn,
        )
        print(f"    -> API ID: {api_id}")
        print(f"       Invoke: http://localhost:4566/restapis/{api_id}/{L['apigateway']['stage']}/_user_request_/")

print("==> Bootstrap complete.")
