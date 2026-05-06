from .heroes import HeroMixin
from .rounds import RoundMixin
from .rules import RulesMixin


class CombatMixin(RulesMixin, HeroMixin, RoundMixin):
    pass
