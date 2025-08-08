from environs import Env

env = Env()
env.read_env()

API_BASE_URL = env.str("API_BASE_URL")

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")

