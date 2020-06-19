# taskmc
Monte carlo estimation of completion dates for taskwarrior. Follows the idea of evidence-based scheduling promote by Joel Spolsky:

https://www.joelonsoftware.com/2007/10/26/evidence-based-scheduling

# Install

Add the user defined attributes (UDAs) `totalactivetime`, `estimatedtime`, and `velocity` to your task configuration:


```
task config uda.totalactivetime.type duration
task config uda.totalactivetime.label Total active time
task config uda.totalactivetime.values ''

task config uda.estimatedtime.type duration
task config uda.estimatedtime.label Estimated time
task config uda.estimatedtime.values ''

task config uda.velocity.type numeric
task config uda.velocity.label Velocity
task config uda.velocity.values ''
```

Or equavalently, add them directly to your .taskrc file:

```
uda.totalactivetime.type=duration
uda.totalactivetime.label=Total active time
uda.totalactivetime.values=''

uda.estimatedtime.type=duration
uda.estimatedtime.label=Estimated time
uda.estimatedtime.values=''

uda.velocity.type=numeric
uda.velocity.label=Velocity
uda.velocity.values=''
```

(So far, the final attribute is not used, but plans are to cache velocities there, which will allow extending predictions to cover tasks in progress.)

These quantities may be added to the `task list` report:

```
task config report.list.labels 'ID,Active,Age,...,Est,Elapsed,Vel,...'
task config report.list.columns 'id,start.age,entry.age,...,estimatedtime,totalactivetime,velocity,...'
```

Then copy the script `taskmc.py` into your home directory, or create an alias as follows:

```
alias taskmc='<directory>/taskmc.py'
```

# Dependencies

This script depends on python 3.7 or above and on the `taskw` python library:

```
pip install taskw
```

This script is made much more useful by the taskwarrior-time-tracking-hook script, available [here](https://github.com/kostajh/taskwarrior-time-tracking-hook):

```
pip install taskwarrior-time-tracking-hook
```

If you install `taskwarrior-time-tracking-hook`, `taskw` will be installed for you.


# Usage

Set estimates for new tasks with

```
task add ... estimatedtime:<integer>seconds
```

Set estimates for already existing tasks with
```
task <task ID> modify estimatedtime:<integer>seconds
```

These may be abbreviated `task add est:<integer>s` and `task <task ID> mod est:<integer>s` if there are no conflicting UDAs.

Set elapsed times for completed tasks as follows:
```
task <task ID> modify totalactivetime:<integer>seconds
```

This may be abbreviated as `task <task ID> mod tot:<integer>s`.

If you have `taskwarrior-time-tracking-hook` installed, you may update elapsed times more conveniently by calling `task <task ID> start` and `task <task ID> stop` before and after working on a task. These may be called an arbitrary number of times on the same task.

When a task is marked as completed (`task <task ID> done`), it begins to be used as a basis for estimating the accuracy of the time estimates and predicting the duration of the remaining tasks. 

An probabilistic estimate for the time remaining to complete all tasks for which estimated times have been specified may then be estimated by calling the script:
```
taskmc.py
```

Because the time remaining is calculated based on the ratio between the estimated times and elapsed time for previously completed tasks, a few tasks with both estimated times and elapsed times must be completed before the output is meaningful.


# Removal

Delete the UDA configuration:
```
task config uda.totalactivetime.type
task config uda.totalactivetime.label
task config uda.totalactivetime.values

task config uda.estimatedtime.type
task config uda.estimatedtime.label
task config uda.estimatedtime.values

task config uda.velocity.type
task config uda.velocity.label
task config uda.velocity.values
```

Remove the Python libraries:

```
pip uninstall taskwarrior-time-tracking-hook
pip uninstall taskw
```

Remove any shell aliases:
```
unalias taskmc
```

And delete the script:
```
rm <Path>/taskmc.py
```
