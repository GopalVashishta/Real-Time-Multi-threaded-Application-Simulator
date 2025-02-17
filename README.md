# Real-Time-Multi-threaded-Application-Simulator
Operating System Project Backend
#Problem Statement:
Description: Develop a simulator to demonstrate multithreading models (e.g., Many-to
One, One-to-Many, Many-to-Many) and thread synchronization using semaphores and 
monitors. The simulator should visualize thread states and interactions, providing insights 
into thread management and CPU scheduling in multi-threaded environments. 

Functionalities of Modules
1. models.py : It contains multi models to simulate threads multithreading(One-to-One, One-to-Many, Many-to-Many).
2. synchronization.py: This file has important classes such as semaphores to control resource locking(mutex in c++), and Monitor which will monitor locks and notify other threads as soon as the lock is released.
3. utils.py : It will make sure safe console output by the Thread.
