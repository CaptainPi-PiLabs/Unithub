from .base import *
from .orbat import *
from .training import *

POLICIES = [
    SectionLeaderPolicy(),
    TrainerPolicy(),
    SeniorTrainerPolicy(),
]