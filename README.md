# Monkey Troop - Readme [![Gitter](https://badges.gitter.im/Project-ARTist/meta.svg)](https://gitter.im/project-artist/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=body_badge)

Monkey Troop is a python program for the evaluation of ARTist Modules and ARTist itself. It executes custom evaluations on multiple connected devices, stores reports and computes results. Evaluations can be resumed after stopping the script.   

A microservice architecture is used where we spawn a new worker process for each device and a central reporter process that collects the results and writes reports. 

## Installation

### Requirements
An installation of python 3.5 and potentially additional python packages are required.      
The evaluation is conducted on arbitrary many devices, but at least one needs to be present.    
Monkey Troop uses the Android developer tools. For example, ```adb``` and ```monkey``` need to be present in the ```PATH ``` to find, control devices and test apps, respectively. 

### Structure

After checking out the repository, the structure looks like follows:

**code/**  
**lists/**  
**scripts/**  

### code/
The root folder for all evaluation-related source files. 
### lists/
Lists of applications to be tested during the evaluation. As they constitute simple text files with one package name per 
line, new lists can be added at will. 
### scripts/
Contains scripts that simplify the evaluation process. The main script, ```evaluate.sh ```, contains the basic invocation 
of the Monkey Troop python tool. However, as different evaluations require different input, there should be another script 
for each evaluation. For example, the trace-logging evaluation uses the ```evaluate_trace.sh ```script that invokes 
```evaluate.sh```with additional arguments. While some arguments are common to all evaluations, concrete evaluations may 
require additional ones. 

## Usage

### Start
The tool is started through the script corresponding to the evaluation that should be conducted. For evaluation ```X```, invoke ```./scripts/evaluate_X.sh```. Scripts need to be started from the tool's base directory. 

### Results
Everytime an application has been tested, Monkey Troop writes a full report to ```out/reports/<pkg>```, where ```<pkg>```is the package name of the tested app. As multiple tasks are executed for each app under test, the report lists success or failure for each of them, accompanied by additional information that might have been obtained during testing. 

In addition, the csv result file in ```out/results``` is extended (or generated if none exists) that shows off a collapsed view of the evaluation results for all tested apps. 

### Cancellation
The evaluation can be cancelled at any time. However, due to its multiprocess-architecture, it might take Monkey Troop a few seconds to terminate all workers since they are given the chance to exit gracefully to avoid data loss. The cancellation signal is triggered with a keyboard interrupt (```Ctrl+C``` on Linux). 

### Resuming
monkey-troop detects previous executions of evaluations and asks whether they should be proceeded. In the positive case, 
already tested apps are skipped and existing results will be updated. In the negative case, all existing evaluation data 
is deleted to allow for a fresh run. You can, however, easily archive your results by backing up the ```out/``` folder. 


## Creating Evaluations

For most evaluations, a lot of boilerplate code already exists, so you do not need to write much code yourself. 
We will guide you through the whole process by creating a sample evaluation. 

### Implementation

Each evaluation resides in its own folder, so we start by creating ```code/evaluations/sample```. 
There are 2 important classes that we need to subclass for our evaluation to work: ```Evaluator``` and ```Worker```.

We first create ```SampleEvaluator```. You can either create it from scratch and get an impression on what and how to do 
from the existing ```TraceLoggingEvaluator```, or you can directly copy paste it and just adapt the code.

The following steps are required:

- set the ```EVAL_ID``` to ```'sample'``` and return this value in the ```get_eval_id``` method.
- define the subtasks that subdivide the execution of a task into logical units. Results and logging will be provided 
for each subtask separately in order to facilitate analysis and debugging. It is recommended to store them in a static 
member and return them in the ```get_subtask_ids_ordered``` method. 
- in order to decide whether a task succeeded, you have to provide *interpretations* that define whether a task is 
an assumption, a requirement or you do not care about its result. 

    - If a required subtask fails, execution stopt here and 
the task is considered a fail. This is typically used for all subtasks that are conducted by the system you are currently 
evaluating. 

    - If an assumption fails, the task will be removed from the final analysis. The idea is that 
you use it to model external factors that you are not in control of, so you can for example retry under different 
circumstances or simply omit these entries from for the final analysis. For example, an application that cannot be 
installed in a device because its Manifest is mumble should not be counted as a failure of your system (assuming 
you did not alter the Manifest). 

    - If a *do not care* subtask fails, it is simply ignored. This is useful if you, for example, model cleanup as a dedicated 
subtask, which might come in handy for debugging and analysis. 

- implement ```init``` by creating an argument parser to obtain evaluation-specific arguments. The dedicated init 
method is required because ```__init__``` is already called earlier and without arguments. 
- you can take ```create_task_queue``` as is for most use cases or adapt if you, e.g., enforce a certain ordering or 
provide more information about a task to the workers. 
- in the ```create_device_worker``` method, return an instance of the ```SampleWorker``` you create in the next step.
- ```get_analyzer``` needs to return a valid analyzer implementation. If you have no special requirements, return an 
instance of the default ```ResultAnalyzer```. It will be used in the ```analyze.py``` script and also during the 
evaluation to display the current state. 
- you also need to define the source for applications under test. ```get_app_repository``` is expected to return an 
```IAppRepository```. If you have all the apk files available, you can simply use ```FileBackedRepository``` that manages 
access to apk files in a directory. If you want to download the apps on the fly, you can also use the 
```GPlayDownloaderRepository``` that makes use of the shipped Google Play Crawler. In this case, however, you need to set 
up the crawler separately as described below. Of course, you can also create an own repository if you need a custom 
solution. 
- finally, put an instance of your ```SampleEvaluation``` in ```Evaluations.py``` with the corresponding id as a key.

In the second step, we create ```SampleWorker``` that carries the main evaluation logic. 
A worker obtains a task from the queue, executes it and collects the results. Therefore, we implement the methods 
```process``` that does the actual execution and ```cleanup``` to takes care of all cleaning tasks. Keep in mind that an 
execution can abort at any point, so a full cleanup is not always required. 

An optional third step is the creation of a custom analyzer. While the default analyzer can check for duplicates and 
displays the current evaluation results, a more customized one can provide evaluation-specific functionality. While 
there are many helper methods readily available, you might want to extend the analyzer's api by adding a new command to 
```get_command_api``` and link the corresponding method. This api is typically triggered by providing the command name 
with additional arguments to ```analyze.py```

### Scripts

The main script to start the evaluation will be created as ```scripts/evaluate_sample.sh```.
Similar to ```evaluate_trace.sh```, it will invoke ```evaluate.sh``` with all the required arguments. 

For the analyzer, you can copy ```scripts/evaluate_trace.sh``` to 
```scripts/evaluate_sample.sh``` and change the eval id from ```trace_logging``` to ```sample```.

## Google Play Crawler

The Google Play Crawler allows to directly download app apk files from the Google Play Store. While monkey-troop itself 
was written from scratch, the crawler is a third-party component with a different license (BSD) and a dedicated 
```README.md```, obtained from [here](https://github.com/egirault/googleplay-api). In order to make use it by, e.g., use the 
```GPlayDownloaderRepository```, you first need to set it up. 

### Setup

The Google Play API requires valid credentials and registered device(s), so you need to provide those information in a 
configuration. First copy ```code/repositories/gplay/googleplay_api/googleplay_api/config.py.example``` to 
```code/repositories/gplay/googleplay_api/googleplay_api/config.py```. Then fill the missing entries with valid 
credentials. If you are unsure about how they might look like, you can check the history of above mentioned GitHub 
project. 
