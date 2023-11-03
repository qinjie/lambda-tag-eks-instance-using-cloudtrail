# Auto-tagging EKS Nodes using CloudTrail EvenBridge and Lambda

How to add a custom tag to EKS nodes when it is launched in EKS cluster? For example, customer would like to tag the respective EC2 instance with 集群名称+节点IP标识, e.g. `pre-eks-01.ip-10-0-22-100`.



### Identify CloudTrail Event

We need to identify which CloudTrail event can provide us the information, e.g. private IP address of the new EC2 instance and cluster name of the EKS cluster. 

1. When a new instance is launched in EKS, we can find traces in CloudTrail. Noticeably, there will be a "RunInstances" event by EKS and Autoscaling respectively. The EKS event contains only the request, whereas the Autoscaling event includes a response with the instance ID value.

![image-20231101172242042](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231101172242042.png)

2. Check the details of RunInstances event of user AutoScaling. Take note that "Event name = RunInstances, Event source = ec2.amazonaws.com, Source IP address = autoscaling.amazonaws.com".

![image-20231101171816094](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231101171816094.png)

3. Examine the event details in JSON format. We will use this JSON object to test our Lambda function later. Refer to `sample_cloudtrail_event.json` file for the sample JSON object.

4. In EventBridge, above event is wrapped in a standard EventBridge object. Replace `<CLOUDTRAIL_EVENT_JSON_OBJECT>` with the JSON object in previous step.

```json
{
  "version": "0",
  "id": "b03f6e6c-1a74-4f69-e219-84e2498d7f20",
  "detail-type": "AWS API Call via CloudTrail",
  "source": "aws.ec2",
  "account": "123456789012",
  "time": "2022-04-01T00:00:00Z",
  "region": "us-east-1",
  "resources": [],
  "detail": <CLOUDTRAIL_EVENT_JSON_OBJECT>
}
```

### Create EventBridge Rule

We will create an EventBridge rule to capture the event when an instance is launched in an EKS cluster.

1. In EventBridge console, create a new rule with type = `"Rule with an event pattern"`. 

![image-20231101173041353](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231101173041353.png)

2. Paste the sample CloudTrail event JSON object as the sample event.

![image-20231103175741549](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103175741549.png)

3. Create a matching event pattern.

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["ec2.amazonaws.com"],
    "eventName": ["RunInstances"],
    "sourceIPAddress": ["autoscaling.amazonaws.com"]
  }
}
```

![image-20231103180147503](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103180147503.png)

4. Click on "Skip to Review and update" to create the rule.



### Create Lambda Function

1. Create a Lambda function `auto-tag-eks-instance` with Python runtime. 

```python
import json
import boto3

def lambda_handler(event, context):
    
    print(event)
    response = event.get('detail', {}).get('responseElements', {})
    items = response.get('instancesSet',{}).get('items',[])
    
    ec2 = boto3.client('ec2')
    
    result = []
    for item in items:
        print(f'item: {item}')
        # Gather instance data
        instance_id = item.get('instanceId')
        tags_list = item.get('tagSet',{}).get('items', [])
        print(f'tags_list: {tags_list}')
        tags = {d.get('key'): d.get('value') for d in tags_list}
        print(f'tags: {tags}')
        cluster_name = tags.get('eks:cluster-name')
        nodegroup_name = tags.get('eks:nodegroup-name')
        network_list = item.get('networkInterfaceSet',{}).get('items',[])
        if network_list:
            privateIpAddress = network_list[0].get('privateIpAddress', '')
            privateDnsName = network_list[0].get('privateDnsName', '')
        else:
            privateIpAddress = ''
            privateDnsName = ''
        
        # Tag instance's Name
        print(f'cluster_name: {cluster_name}, nodegroup_name: {nodegroup_name}, privateIpAddress: {privateIpAddress}')
        if cluster_name and nodegroup_name and privateIpAddress:
            name_value = f'{cluster_name}-{nodegroup_name}-ip-{privateIpAddress}'
            print(f'Tagging EKS Instance: name = {name_value}')
            ec2.create_tags(Resources=[instance_id], Tags=[{'Key':'Name', 'Value': name_value}])
            result.append({'Key':'Name', 'Value': name_value})
        
    return {
        'statusCode': 200,
        'body': result
    }
```

2. Modify its execution role to allow action `"ec2:CreateTags"`.

```json
{
  "Effect": "Allow",
  "Action": "ec2:CreateTags",
  "Resource": "*"
}
```

![image-20231103183049025](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103183049025.png)

![image-20231103183246281](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103183246281.png)

3. Add a trigger with above EventBridge rule "eke-run-instances". 

![image-20231103183405041](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103183405041.png)

![image-20231103183455894](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103183455894.png)

4. Test the Lambda function with the CloudTrail event JSON object. Note: it will fail because the instance ID doesn't exists.

![image-20231103183619653](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103183619653.png)



### Test

Test to make sure Lambda function is triggered when new EC2 instance(s) are launched in EKS cluster.

1. In an existing EKS cluster, create a new node group with 2 desired nodes.

![image-20231103174120840](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103174120840.png)

2. Examine the instances in EC2 console. It is tagged with `Name = <CLUSTER_NAME>-<NODE_GROUP_NAME>-ip-<PRIVATE_IP>`.

![image-20231103174651957](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231103174651957.png)

