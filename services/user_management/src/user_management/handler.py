from mangum import Mangum
import app

handler = Mangum(app)
