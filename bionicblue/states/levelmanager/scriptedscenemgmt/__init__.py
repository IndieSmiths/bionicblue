"""Facility with class extension for managing scripted scenes."""

from .preprocessing import ScriptedScenePreprocessing
from .loopmgmt import ScriptedSceneLoopManagement



class ScriptedSceneManagement(
    ScriptedScenePreprocessing,
    ScriptedSceneLoopManagement,
):
    """Class extension to enable scripted scene management."""
