import json
import boto3

# setup clients
dynamodb_client = boto3.resource('dynamodb')
autoscaling_client = boto3.client('autoscaling')

def hello(event, context):

    type_of_scaling = event

    if type_of_scaling != 'scale_down' and type_of_scaling != 'scale_up':
        response_json = {
            'status': 'Failure',
            'type_of_scaling': type_of_scaling,
            'error': 'invalid type of scaling'
        }
        # create a response
        response = {
            "statusCode": 400,
            "body": json.dumps(response_json)
        }
        return response

    # get the apps from dynamo db table "BeanstalkScaling"
    table = dynamodb_client.Table("BeanstalkScaling")
    result = table.get_item(
        Key={
            'type_of_scaling': type_of_scaling
        }
    )

    # print(result)
    # print(result['Item'])

    applications_to_scale = result['Item']['applications_to_scale']
    desired_min = result['Item']['desired_min']
    desired_max = result['Item']['desired_max']
    desired_capacity = result['Item']['desired_capacity']

    # print(applications_to_scale)
    # print(desired_min)
    # print(desired_max)
    # print(desired_capacity)

    # get the autoscaling groups by tag
    response_describe_autoscaling_groups = autoscaling_client.describe_auto_scaling_groups(
        MaxRecords=100
    )
    # print(response_describe_autoscaling_groups)

    # filter
    list_of_applications = list(filter(lambda x: [el for el in x['Tags'] if el['Value'] in applications_to_scale], response_describe_autoscaling_groups['AutoScalingGroups']))

    for application in list_of_applications:
        print(application)
        response = autoscaling_client.update_auto_scaling_group(
            AutoScalingGroupName=application['AutoScalingGroupName'],
            MinSize=int(desired_min),
            MaxSize=int(desired_max),
            DesiredCapacity=int(desired_capacity)
        )

    response_json = {
        'status': 'Success',
        'applications_to_scale': applications_to_scale,
        'desired_min': desired_min,
        'desired_max': desired_max,
        'desired_capacity': desired_capacity
    }

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(response_json)
    }

    return response
