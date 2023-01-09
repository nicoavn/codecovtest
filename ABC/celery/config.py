import kombu


def celery_config(broker_url, queue_name='celery', **kwargs):
    """
    Create the Celery config used in our application config files.

    For more info on task priority support, see:

        - https://github.com/celery/celery/issues/2635
        - https://stackoverflow.com/questions/43618214/celery-task-priority
        - http://docs.celeryproject.org/en/latest/userguide/calling.html#advanced-options
    """
    config = {
        'broker_url': broker_url,
        # Setup a queue that is ready for prioritized tasks.  The queue has to be created this way,
        # once created in rabbitmq, the setting can't be changed.  This can be set without any
        # penalty for an app that won't use prioritized tasks.
        'task_queues': (
            kombu.Queue(
                queue_name,
                kombu.Exchange(queue_name),
                routing_key=queue_name,
                queue_arguments={'x-max-priority': 5},
            ),
        ),
        # The default queue should be the one we just setup that has priority support.
        'task_default_queue': queue_name,
        # Worker processes die and respawn after this many tasks.  Helps mitigate small memory
        # leaks.
        'worker_max_tasks_per_child': 2000,
        # In order for task priority to work effectively, we don't want our workers to pre-load
        # tasks.  Use 1 to instruct each worker to only pre-load 1 task.  That means each worker
        # will have the task it's currently processing plus one additional that was pre-loaded.  See
        # http://docs.celeryproject.org/en/latest/userguide/optimizing.html#reserve-one-task-at-a-time
        # for more info.
        #
        # The docs say you may want to use `task_acks_late` as well.  However, this would mean that
        # we possibly double-execute a task in case of mid-task failure.  Since most of our tasks
        # are not idempotent, it seems better to have our priority execution affected just a bit
        # rather than double-execute a prioritized task.
        #
        # Uncomment this setting if you plan to use prioritized tasks.
        # 'worker_prefetch_multiplier': 1,
    }

    config.update(kwargs)

    return config
