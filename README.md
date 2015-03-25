# boundary-riskapi-plugin

Boundary Plugin for StatPro Riskapi

### Prerequisites

|     OS    | Linux | Windows | SmartOS | OS X |
|:----------|:-----:|:-------:|:-------:|:----:|
| Supported |   v   |         |         |      |

|  Runtime | node.js | Python | Java |
|:---------|:-------:|:------:|:----:|
| Required |         |    +   |      |

### Plugin Setup

None

#### Plugin Configuration Fields

|Field Name   |Description                                                                         |
|:------------|:-----------------------------------------------------------------------------------|
|Poll Interval|The Poll Interval to call the command in milliseconds. Defaults to 1000 milliseconds|
|Hostname     |IP Address or hostname that contains the RabbitMQ instance                          |
|Port         |Listening port of the RabbitMQ management plugin                                    |
|User         |User name to use for authenticate against the RabbitMQ management plugin            |
|Password     |Password to use for authenticate against the RabbitMQ management plugin             |

### Metrics Collected
|Metric Name                                             |Description                             |
|:-------------------------------------------------------|:---------------------------------------|
|STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN         |Compute time (mean)                     |
|STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_50           |Compute time (mode)                     |
|STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_95           |Computation time (95th percentile)      |
|STATPRO_RISKAPI_OVERALL_ERRORS_COUNT                    |Errors (count)                          |
|STATPRO_RISKAPI_OVERALL_ERRORS_ONE                      |Errors (mean over 1min)                 |
|STATPRO_RISKAPI_OVERALL_THROUGHPUT_COUNT                |Throughput (count)                      |
|STATPRO_RISKAPI_OVERALL_THROUGHPUT_ONE                  |Through put (mean over 1min)            |
|STATPRO_RISKAPI_OVERALL_TIME_ARITHMETIC_MEAN            |Total time (mean)                       |
|STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_50              |Total time (mode)                       |
|STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_95              |Total time (95th percentile)            |
|STATPRO_RISKAPI_QUEUE_LENGTH_RAPI                       |Request Queue Length                    |
|STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_ARITHMETIC_MEAN |Enqueued Request Time (mean)            |
|STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_50   |Enqueued Request Time (mode)            |
|STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_95   |Enqueued Request Time (95th percentile) |
|STATPRO_RISKAPI_THROUGHPUT_RAPI_COUNT                   |Throughput (count)                      |
|STATPRO_RISKAPI_THROUGHPUT_RAPI_ONE                     |Throughput (mean over 1min)             |
