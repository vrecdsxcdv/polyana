from config import config

def is_operator_user(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

def is_operator_chat(chat_id: int) -> bool:
    # Команда доступна только в операторском групповом чате
    return bool(getattr(config, "OPERATOR_CHAT_ID", 0)) and chat_id == config.OPERATOR_CHAT_ID

def can_run_operator_command(user_id: int, chat_id: int) -> bool:
    # Должно выполняться ОДНОВРЕМЕННО: чат = операторский И user_id в ADMIN_IDS
    return is_operator_chat(chat_id) and is_operator_user(user_id)




