from listeners import ListenerManager, ListenerManagerDecorator


class OnPlayerChangeHero(ListenerManagerDecorator):
    manager = ListenerManager()


class OnHeroLevelUp(ListenerManagerDecorator):
    manager = ListenerManager()
