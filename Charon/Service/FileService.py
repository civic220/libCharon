import dbus

import Queue
import Job

class FileService(dbus.service.Object):
    def __init__(self, dbus_bus: dbus.Bus):
        super().__init__(
            bus_name = dbus.service.BusName("nl.ultimaker.charon", dbus_bus),
            object_path = "/nl/ultimaker/charon"
        )

        self.__queue = Queue.Queue()

    ##  Start a request for data from a file.
    #
    #   This function will start a request for data from a certain file.
    #   It will be processed in a separate thread.
    #
    #   When the request has finished, `requestFinished` will be emitted.
    #
    #   \param request_id A unique identifier to track this request with.
    #   \param file_path The path to a file to load.
    #   \param virtual_paths A list of virtual paths that define what set of data to retrieve.
    #
    #   \return A boolean indicating whether the request was successfully started.
    @dbus.decorators.method("nl.ultimaker.charon", "ssas", "b")
    def startRequest(self, request_id, file_path, virtual_paths):
        job = Job.Job(self, request_id, file_path, virtual_paths)
        return self.__queue.enqueue(job)

    ##  Cancel a pending request for data.
    #
    #   This will cancel a request that was previously posted.
    #
    #   Note that if the request is already being processed, the request will not be
    #   canceled. If the cancel was successful, `requestError` will be emitted with the
    #   specified request and an error string describing it was canceled.
    #
    #   \param request_id The ID of the request to cancel.
    @dbus.decorators.method("nl.ultimaker.charon", "s", "")
    def cancelRequest(self, request_id):
        if self.__queue.dequeue(request_id):
            self.requestError(request_id, "Request canceled")

    ##  Emitted whenever data for a request is available.
    #
    #   This will be emitted while a request is processing and requested data has become
    #   available.
    #
    #   \param request_id The ID of the request that data is available for.
    #   \param data A dictionary with virtual paths and data for those paths.
    @dbus.decorators.signal("nl.ultimaker.charon", "sa{sv}")
    def requestData(self, request_id, data):
        pass

    ##  Emitted whenever a request for data has been completed.
    #
    #   This signal will be emitted once a request is completed successfully.
    #
    #   \param request_id The ID of the request that completed.
    @dbus.decorators.signal("nl.ultimaker.charon", "s")
    def requestCompleted(self, request_id):
        pass

    ##  Emitted whenever a request that is processing encounters an error.
    #
    #   \param request_id The ID of the request that encountered an error.
    #   \param error_string A string describing the error.
    @dbus.decorators.signal("nl.ultimaker.charon", "ss")
    def requestError(self, request_id, error_string):
        pass
