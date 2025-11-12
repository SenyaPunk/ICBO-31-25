schedule_notifier = None


def set_notifier(notifier):
    """Устанавливает глобальный экземпляр notifier"""
    global schedule_notifier
    schedule_notifier = notifier


def get_notifier():
    """Возвращает глобальный экземпляр notifier"""
    return schedule_notifier
