"""Facility with class extension for managing scripted scenes."""

from .preprocessing import ScriptedScenePreprocessing
from .loopmanagement import ScriptedSceneLoopManagement



class ScriptedSceneManagement(
    ScriptedScenePreprocessing,
    ScriptedSceneLoopManagement,
):
    """Class extension to enable scripted scene management."""
