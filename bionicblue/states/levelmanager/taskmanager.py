"""Facility for time related execution."""

### standard library import
from math import inf as INFINITY


### local import
from ...pygamesetup.constants import FPS



MILLISECS_PER_FRAME = 1000 / FPS


class TaskManager:
    """Manages task objects between differents levels."""

    def __init__(self):
        """Assign variables."""

        self.tasks = []
        self.sendoff_tasks = []

    def clear(self):
        """Set defaults and perform setups."""
        self.tasks.clear()

        for task in self.sendoff_tasks:
            try:
                task()
            except Exception as err:
                err_msg = str(err)
                print(err_msg)

        self.sendoff_tasks.clear()

    def update(self):
        """Update tasks."""

        finished_tasks = []

        for task in self.tasks:

            try:
                task.update()

            except Exception as err:

                err_msg = str(err)
                print(err_msg)

                task.finished = True

            if task.finished:
                finished_tasks.append(task)

        for task in finished_tasks:
            self.tasks.remove(task)

    def append_ready_task(
        self,
        callable_task,
        cyclic=False,
    ):
        """Instantiate and store task ready to be executed. Also return it.

        callable_task
            Callable to be executed as soon as task updates.
        cyclic
            Boolean. If True, the task will execute indefinitely, until either
            its "finished" attribute is manually changed to True or the level
            ends. Defaults to False.
        """
        task = ReadyTask(callable_task, cyclic)
        self.tasks.append(task)

        return task

    def append_conditional_task(
        self,
        callable_task,
        boolean_func,
        cyclic=False,
    ):
        """Instantiate and store conditional task. Also return it.

        callable_task
            Callable to be executed when condition is found to be True.
        boolean_func
            Callable executed every frame. When its return value is truthy
            the task's callable is executed and the task is considered
            finished.
        cyclic
            Boolean. If True, the task will execute every frame it finds the
            return value of boolean_func() to be True, until either its
            "finished" attribute is manually changed to True or the level
            ends. Defaults to False, which means the task is executed only
            once, the first time boolean_func() returns True.
        """
        task = ConditionalTask(callable_task, boolean_func, cyclic)
        self.tasks.append(task)

        return task

    def append_timed_task(
        self,
        callable_task,
        delta_t,
        unit='milliseconds',
        cyclic=False,
    ):
        """Instantiate and store timed task. Also return it.

        callable_task
            Callable to be executed when delta_t is reached.
        delta_t
            Time interval measured in milliseconds or frames.
        unit
            String hinting if time interval (delta_t) is measured in
            milliseconds or frames. Defaults to 'milliseconds'.
        cyclic
            Boolean. If True, the task will execute indefinitely, each time to
            specified interval elapses, until either its "finished" attribute
            is manually changed to True or the level ends. Defaults to False.
        """
        task = TimedTask(callable_task, delta_t, unit, cyclic)
        self.tasks.append(task)

        return task

    def append_sendoff_task(self, callable_task):
        """Store a callable to call before leaving level.

        callable_task
            A callable to be called before exiting a level.
            Callables are executed in the self.clear method.
        """
        self.sendoff_tasks.append(callable_task)


class ReadyTask:
    """A task which executes no matter what."""

    def __init__(
        self,
        callable_task,
        cyclic=False,
    ):
        """Assign variables.

        callable_task
            Callable to be executed as soon as task updates.
        cyclic
            Boolean. If True, the task will execute indefinitely, until either
            its "finished" attribute is manually changed to True or the level
            ends. Defaults to False.
        """
        self.finished = False
        self.invoke = callable_task

        self.update = (

            self.invoke
            if cyclic

            else self.execute_once

        )

    def execute_once(self):
        """Execute and finish task."""

        self.invoke()
        self.finished = True

    def get_remaining(self):
        """Get remaining time.

        Since this tasks is always ready to execute. Remaining time is always zero.
        """
        return 0


class ConditionalTask:
    """A task which executes after a condition is True."""

    def __init__(
        self, 
        callable_task,
        boolean_func,
        cyclic=False,
    ):
        """Assign variables.

        callable_task
            Callable to be executed when condition is found to be True.
        boolean_func
            Callable executed every frame. When its return value is truthy
            the task's callable is executed and the task is considered
            finished.
        cyclic
            Boolean. If True, the task will execute every frame it finds the
            return value of boolean_func() to be True, until either its
            "finished" attribute is manually changed to True or the level
            ends. Defaults to False, which means the task is executed only
            once, the first time boolean_func() returns True.
        """
        self.finished = False

        self.invoke = callable_task
        self.boolean_func = boolean_func

        self.execute = (

            self.invoke
            if cyclic

            else self.execute_once

        )

    def update(self):
        """Check condition and execute task if True."""

        if self.boolean_func():
            self.execute()

    def execute_once(self):
        """Execute and finish task."""

        self.invoke()
        self.finished = True

    def get_remaining(self):
        """Get remaining time.

        Since there's no way to know, we decided to return infinity to indicate
        maximum waiting time.
        """
        return INFINITY

    

class TimedTask:
    """A task which executes after a time interval.

    Tasks are scheduled either in milliseconds or in frames.
    They can be executed only once or repeatedly.
    """

    def __init__(
        self,
        callable_task,
        delta_t,
        unit='milliseconds',
        cyclic=False,
    ):
        """Assign variables.

        callable_task
            Callable to be executed when delta_t is reached.
        delta_t
            Time interval measured in milliseconds or frames.
        unit
            String hinting if time interval (delta_t) is measured in
            milliseconds or frames. Defaults to 'milliseconds'.
        cyclic
            Boolean. If True, the task will execute indefinitely, each time to
            specified interval elapses, until either its "finished" attribute
            is manually changed to True or the level ends. Defaults to False.
        """
        self.finished = False

        self.delta_t = delta_t
        self.invoke = callable_task

        self.start = 0

        self.increment = (

            MILLISECS_PER_FRAME
            if unit == 'milliseconds'

            else 1

        )

        self.execute = (

            self.execute_cyclic
            if cyclic

            else self.execute_once
        )

    def update(self):
        """Increment count."""

        if self.start >= self.delta_t:
            self.execute()

        self.start += self.increment

    def execute_once(self):
        """Execute and finish task."""
        self.invoke()
        self.finished = True

    def execute_cyclic(self):
        """Execute and restart another cycle."""
        self.invoke()
        self.start = 0

    def get_remaining(self):
        """Get remaining time."""
        if not self.finished:
            return self.delta_t - round(self.start)

        else:
            return 0



TASK_MANAGER = TaskManager()

append_ready_task = TASK_MANAGER.append_ready_task
append_conditional_task = TASK_MANAGER.append_conditional_task
append_timed_task = TASK_MANAGER.append_timed_task

append_sendoff_task = TASK_MANAGER.append_sendoff_task

clear_task_manager = TASK_MANAGER.clear
update_task_manager = TASK_MANAGER.update
