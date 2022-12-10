# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# See include/mesos/scheduler.hpp, include/mesos/executor.hpp and
# include/mesos/mesos.proto for more information documenting this
# interface.

"""Python bindings for Mesos."""

from __future__ import print_function

import sys

__all__ = (
  'Executor',
  'ExecutorDriver',
  'Scheduler',
  'SchedulerDriver',
)

class Scheduler(object):
  """
    Base class for Mesos schedulers. Users' schedulers should extend this
    class to get default implementations of methods they don't override.
  """

  def registered(self, driver, frameworkId, masterInfo):
    """
      Invoked when the scheduler successfully registers with a Mesos master.
      It is called with the frameworkId, a unique ID generated by the
      master, and the masterInfo which is information about the master
      itself.
    """

  def reregistered(self, driver, masterInfo):
    """
      Invoked when the scheduler reregisters with a newly elected Mesos
      master.  This is only called when the scheduler has previously been
      registered.  masterInfo contains information about the newly elected
      master.
    """

  def disconnected(self, driver):
    """
      Invoked when the scheduler becomes disconnected from the master, e.g.
      the master fails and another is taking over.
    """

  def resourceOffers(self, driver, offers):
    """
      Invoked when resources have been offered to this framework. A single
      offer will only contain resources from a single slave.  Resources
      associated with an offer will not be re-offered to _this_ framework
      until either (a) this framework has rejected those resources (see
      SchedulerDriver.launchTasks) or (b) those resources have been
      rescinded (see Scheduler.offerRescinded).  Note that resources may be
      concurrently offered to more than one framework at a time (depending
      on the allocator being used).  In that case, the first framework to
      launch tasks using those resources will be able to use them while the
      other frameworks will have those resources rescinded (or if a
      framework has already launched tasks with those resources then those
      tasks will fail with a TASK_LOST status and a message saying as much).
    """

  def offerRescinded(self, driver, offerId):
    """
      Invoked when an offer is no longer valid (e.g., the slave was lost or
      another framework used resources in the offer.) If for whatever reason
      an offer is never rescinded (e.g., dropped message, failing over
      framework, etc.), a framework that attempts to launch tasks using an
      invalid offer will receive TASK_LOST status updates for those tasks
      (see Scheduler.resourceOffers).
    """

  def statusUpdate(self, driver, status):
    """
      Invoked when the status of a task has changed (e.g., a slave is
      lost and so the task is lost, a task finishes and an executor
      sends a status update saying so, etc). If implicit
      acknowledgements are being used, then returning from this
      callback _acknowledges_ receipt of this status update! If for
      whatever reason the scheduler aborts during this callback (or
      the process exits) another status update will be delivered (note,
      however, that this is currently not true if the slave sending the
      status update is lost/fails during that time). If explicit
      acknowledgements are in use, the scheduler must acknowledge this
      status on the driver.
    """

  def frameworkMessage(self, driver, executorId, slaveId, message):
    """
      Invoked when an executor sends a message. These messages are best
      effort; do not expect a framework message to be retransmitted in any
      reliable fashion.
    """

  def slaveLost(self, driver, slaveId):
    """
      Invoked when a slave has been determined unreachable (e.g., machine
      failure, network partition.) Most frameworks will need to reschedule
      any tasks launched on this slave on a new slave.

      NOTE: This callback is not reliably delivered. If a host or
      network failure causes messages between the master and the
      scheduler to be dropped, this callback may not be invoked.
    """

  def executorLost(self, driver, executorId, slaveId, status):
    """
      Invoked when an executor has exited/terminated. Note that any tasks
      running will have TASK_LOST status updates automatically generated.

      NOTE: This callback is not reliably delivered. If a host or
      network failure causes messages between the master and the
      scheduler to be dropped, this callback may not be invoked.
    """

  def error(self, driver, message):
    """
      Invoked when there is an unrecoverable error in the scheduler or
      scheduler driver.  The driver will be aborted BEFORE invoking this
      callback.
    """
    print("Error from Mesos: %s " % message, file=sys.stderr)


class SchedulerDriver(object):
  """
    Interface for Mesos scheduler drivers. Users may wish to implement this
    class in mock objects for tests.
  """
  def start(self):
    """
      Starts the scheduler driver.  This needs to be called before any other
      driver calls are made.
    """

  def stop(self, failover=False):
    """
      Stops the scheduler driver. If the 'failover' flag is set to False
      then it is expected that this framework will never reconnect to Mesos
      and all of its executors and tasks can be terminated.  Otherwise, all
      executors and tasks will remain running (for some framework specific
      failover timeout) allowing the scheduler to reconnect (possibly in the
      same process, or from a different process, for example, on a different
      machine.)
    """

  def abort(self):
    """
      Aborts the driver so that no more callbacks can be made to the
      scheduler.  The semantics of abort and stop have deliberately been
      separated so that code can detect an aborted driver (i.e., via the
      return status of SchedulerDriver.join), and instantiate and start
      another driver if desired (from within the same process.)
    """

  def join(self):
    """
      Waits for the driver to be stopped or aborted, possibly blocking the
      current thread indefinitely.  The return status of this function can
      be used to determine if the driver was aborted (see mesos.proto for a
      description of Status).
    """

  def run(self):
    """
      Starts and immediately joins (i.e., blocks on) the driver.
    """

  def requestResources(self, requests):
    """
      Requests resources from Mesos (see mesos.proto for a description of
      Request and how, for example, to request resources from specific
      slaves.)  Any resources available are offered to the framework via
      Scheduler.resourceOffers callback, asynchronously.
    """

  def launchTasks(self, offerIds, tasks, filters=None):
    """
      Launches the given set of tasks. Any remaining resources (i.e.,
      those that are not used by the launched tasks or their executors)
      will be considered declined. Note that this includes resources
      used by tasks that the framework attempted to launch but failed
      (with TASK_ERROR) due to a malformed task description. The
      specified filters are applied on all unused resources (see
      mesos.proto for a description of Filters). Available resources
      are aggregated when multiple offers are provided. Note that all
      offers must belong to the same slave. Invoking this function with
      an empty collection of tasks declines offers in their entirety
      (see Scheduler.declineOffer). Note that passing a single offer
      is also supported.
    """

  def killTask(self, taskId):
    """
      Kills the specified task. Note that attempting to kill a task is
      currently not reliable.  If, for example, a scheduler fails over while
      it was attempting to kill a task it will need to retry in the future.
      Likewise, if unregistered / disconnected, the request will be dropped
      dropped (these semantics may be changed in the future).
    """

  def acceptOffers(self, offerIds, operations, filters=None):
    """
      Accepts the given offers and performs a sequence of operations on
      those accepted offers. See Offer.Operation in mesos.proto for the
      set of available operations. Any remaining resources (i.e., those
      that are not used by the launched tasks or their executors) will
      be considered declined. Note that this includes resources used by
      tasks that the framework attempted to launch but failed (with
      TASK_ERROR) due to a malformed task description. The specified
      filters are applied on all unused resources (see mesos.proto for
      a description of Filters). Available resources are aggregated
      when multiple offers are provided. Note that all offers must
      belong to the same slave.
    """

  def declineOffer(self, offerId, filters=None):
    """
      Declines an offer in its entirety and applies the specified
      filters on the resources (see mesos.proto for a description of
      Filters). Note that this can be done at any time, it is not
      necessary to do this within the Scheduler::resourceOffers
      callback.
    """

  def reviveOffers(self, roles=None):
    """
      Removes filters either for all roles of the framework (if 'roles'
      is None) or for the specified roles and removes these roles from
      the suppressed set.  If the framework is not connected to the master,
      an up-to-date set of suppressed roles will be sent to the master
      during re-registration.

      NOTE: If 'roles' is an empty iterable, this method does nothing.
    """

  def suppressOffers(self, roles=None):
    """
      Informs Mesos master to stop sending offers either for all roles
      of the framework (if 'roles' is None) or for the specified 'roles'
      of the framework (i.e. to suppress these roles). To resume getting
      offers, the scheduler can call reviveOffers() or set the suppressed
      roles explicitly via updateFramework().

      NOTE: If the framework is not connected to the master, an up-to-date set
      of suppressed roles will be sent to the master during re-registration.

      NOTE: If `roles` is an empty iterable, this method does nothing.
    """

  def acknowledgeStatusUpdate(self, status):
    """
      Acknowledges the status update. This should only be called
      once the status update is processed durably by the scheduler.
      Not that explicit acknowledgements must be requested via the
      constructor argument, otherwise a call to this method will
      cause the driver to crash.
    """

  def sendFrameworkMessage(self, executorId, slaveId, data):
    """
      Sends a message from the framework to one of its executors. These
      messages are best effort; do not expect a framework message to be
      retransmitted in any reliable fashion.
    """

  def reconcileTasks(self, tasks):
    """
      Allows the framework to query the status for non-terminal tasks.
      This causes the master to send back the latest task status for
      each task in 'statuses', if possible. Tasks that are no longer
      known will result in a TASK_LOST update. If statuses is empty,
      then the master will send the latest status for each task
      currently known.
    """

  def updateFramework(self, frameworkInfo, suppressedRoles):
    """
      Inform Mesos master about changes to the `FrameworkInfo` and
      the set of suppressed roles. The driver will store the new
      `FrameworkInfo` and the new set of suppressed roles, and all
      subsequent re-registrations will use them.

      NOTE: If the supplied info is invalid or fails authorization,
      the `error()` callback will be invoked asynchronously (after
      the master replies with a `FrameworkErrorMessage`).

      NOTE: This must be called after initial registration with the
      master completes and the `FrameworkID` is assigned. The assigned
      `FrameworkID` must be set in `frameworkInfo`.

      NOTE: The `FrameworkInfo.user` and `FrameworkInfo.hostname`
      fields will be auto-populated using the same approach used
      during driver initialization.
    """

class Executor(object):
  """
    Base class for Mesos executors. Users' executors should extend this
    class to get default implementations of methods they don't override.
  """

  def registered(self, driver, executorInfo, frameworkInfo, slaveInfo):
    """
      Invoked once the executor driver has been able to successfully connect
      with Mesos.  In particular, a scheduler can pass some data to its
      executors through the FrameworkInfo.ExecutorInfo's data field.
    """

  def reregistered(self, driver, slaveInfo):
    """
      Invoked when the executor reregisters with a restarted slave.
    """

  def disconnected(self, driver):
    """
      Invoked when the executor becomes "disconnected" from the slave (e.g.,
      the slave is being restarted due to an upgrade).
    """

  def launchTask(self, driver, task):
    """
      Invoked when a task has been launched on this executor (initiated via
      Scheduler.launchTasks).  Note that this task can be realized with a
      thread, a process, or some simple computation, however, no other
      callbacks will be invoked on this executor until this callback has
      returned.
    """

  def killTask(self, driver, taskId):
    """
      Invoked when a task running within this executor has been killed (via
      SchedulerDriver.killTask).  Note that no status update will be sent on
      behalf of the executor, the executor is responsible for creating a new
      TaskStatus (i.e., with TASK_KILLED) and invoking ExecutorDriver's
      sendStatusUpdate.
    """

  def frameworkMessage(self, driver, message):
    """
      Invoked when a framework message has arrived for this executor.  These
      messages are best effort; do not expect a framework message to be
      retransmitted in any reliable fashion.
    """

  def shutdown(self, driver):
    """
      Invoked when the executor should terminate all of its currently
      running tasks.  Note that after Mesos has determined that an executor
      has terminated any tasks that the executor did not send terminal
      status updates for (e.g., TASK_KILLED, TASK_FINISHED, TASK_FAILED,
      etc) a TASK_LOST status update will be created.
    """

  def error(self, driver, message):
    """
      Invoked when a fatal error has occurred with the executor and/or
      executor driver.  The driver will be aborted BEFORE invoking this
      callback.
    """
    print("Error from Mesos: %s" % message, file=sys.stderr)



class ExecutorDriver(object):
  """
    Interface for Mesos executor drivers. Users may wish to extend this
    class in mock objects for tests.
  """
  def start(self):
    """
      Starts the executor driver. This needs to be called before any other
      driver calls are made.
    """

  def stop(self):
    """
      Stops the executor driver.
    """

  def abort(self):
    """
      Aborts the driver so that no more callbacks can be made to the
      executor.  The semantics of abort and stop have deliberately been
      separated so that code can detect an aborted driver (i.e., via the
      return status of ExecutorDriver.join), and instantiate and start
      another driver if desired (from within the same process, although this
      functionality is currently not supported for executors).
    """

  def join(self):
    """
      Waits for the driver to be stopped or aborted, possibly blocking the
      current thread indefinitely.  The return status of this function can
      be used to determine if the driver was aborted (see mesos.proto for a
      description of Status).
    """

  def run(self):
    """
      Starts and immediately joins (i.e., blocks on) the driver.
    """

  def sendStatusUpdate(self, status):
    """
      Sends a status update to the framework scheduler, retrying as
      necessary until an acknowledgement has been received or the executor
      is terminated (in which case, a TASK_LOST status update will be sent).
      See Scheduler.statusUpdate for more information about status update
      acknowledgements.
    """

  def sendFrameworkMessage(self, data):
    """
      Sends a message to the framework scheduler. These messages are best
      effort; do not expect a framework message to be retransmitted in any
      reliable fashion.
    """
