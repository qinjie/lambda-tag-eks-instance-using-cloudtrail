# Auto-tagging EKS Nodes using CloudTrail EvenBridge and Lambda

How to add a custom tag to EKS nodes when it is launched in EKS cluster? For example, customer would like to tag the respective EC2 instance with 集群名称+节点IP标识, e.g. `pre-eks-01.ip-10-0-22-100`.



### Identify CloudTrail Event

We need to identify which CloudTrail event can provide us the information, e.g. private IP address of the new EC2 instance and cluster name of the EKS cluster. 

1. When a new instance is launched in EKS, we can find traces in CloudTrail. Noticeably, there will be a "RunInstances" event by EKS and Autoscaling respectively. The EKS event contains only the request, whereas the Autoscaling event includes a response with the instance ID value.

![image-20231101172242042](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231101172242042.png)

2. Check the details of RunInstances event of user AutoScaling. Take note that "Event name = RunInstances, Event source = ec2.amazonaws.com, Source IP address = autoscaling.amazonaws.com".

![image-20231101171816094](./assets.Auto-tagging%20EKS%20Nodes%20using%20CloudTrail%20EvenBridge%20and%20Lambda/image-20231101171816094.png)

3. Examine the event details in JSON format. We will use this JSON object to test our Lambda function later. Here is a sample JSON file.

```json
{
    "eventVersion": "1.08",
    "userIdentity": {
        "type": "AssumedRole",
        "principalId": "AROAWWNJHDG5EZDO4IS5S:AutoScaling",
        "arn": "arn:aws:sts::460453255610:assumed-role/AWSServiceRoleForAutoScaling/AutoScaling",
        "accountId": "460453255610",
        "sessionContext": {
            "sessionIssuer": {
                "type": "Role",
                "principalId": "AROAWWNJHDG5EZDO4IS5S",
                "arn": "arn:aws:iam::460453255610:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling",
                "accountId": "460453255610",
                "userName": "AWSServiceRoleForAutoScaling"
            },
            "webIdFederationData": {},
            "attributes": {
                "creationDate": "2023-11-01T08:02:36Z",
                "mfaAuthenticated": "false"
            }
        },
        "invokedBy": "autoscaling.amazonaws.com"
    },
    "eventTime": "2023-11-01T08:02:37Z",
    "eventSource": "ec2.amazonaws.com",
    "eventName": "RunInstances",
    "awsRegion": "ap-southeast-1",
    "sourceIPAddress": "autoscaling.amazonaws.com",
    "userAgent": "autoscaling.amazonaws.com",
    "requestParameters": {
        "instancesSet": {
            "items": [
                {
                    "minCount": 1,
                    "maxCount": 1
                }
            ]
        },
        "instanceType": "t3.medium",
        "blockDeviceMapping": {},
        "availabilityZone": "ap-southeast-1b",
        "monitoring": {
            "enabled": false
        },
        "disableApiTermination": false,
        "disableApiStop": false,
        "clientToken": "fleet-1fb4718e-e78e-4e3e-0c18-ad80e56dbf97-0",
        "networkInterfaceSet": {
            "items": [
                {
                    "deviceIndex": 0,
                    "subnetId": "subnet-08f460ce5d424d980"
                }
            ]
        },
        "tagSpecificationSet": {
            "items": [
                {
                    "resourceType": "instance",
                    "tags": [
                        {
                            "key": "aws:autoscaling:groupName",
                            "value": "eks-test2-06c5c4f3-8ec0-78ca-429c-84bcfac2302e"
                        },
                        {
                            "key": "eks:cluster-name",
                            "value": "test"
                        },
                        {
                            "key": "kubernetes.io/cluster/test",
                            "value": "owned"
                        },
                        {
                            "key": "eks:nodegroup-name",
                            "value": "test2"
                        },
                        {
                            "key": "k8s.io/cluster-autoscaler/enabled",
                            "value": "true"
                        },
                        {
                            "key": "k8s.io/cluster-autoscaler/test",
                            "value": "owned"
                        },
                        {
                            "key": "aws:ec2:fleet-id",
                            "value": "fleet-1fb4718e-e78e-4e3e-0c18-ad80e56dbf97"
                        }
                    ]
                }
            ]
        },
        "launchTemplate": {
            "launchTemplateId": "lt-06859e733591a6c06",
            "version": "1"
        }
    },
    "responseElements": {
        "requestId": "7c5d5def-467d-426a-ba36-93df8499dda8",
        "reservationId": "r-0ab238e5fdca26960",
        "ownerId": "460453255610",
        "groupSet": {},
        "instancesSet": {
            "items": [
                {
                    "instanceId": "i-0a3c844322fab4955",
                    "imageId": "ami-08bc1ca764d8b6c59",
                    "currentInstanceBootMode": "legacy-bios",
                    "instanceState": {
                        "code": 0,
                        "name": "pending"
                    },
                    "privateDnsName": "ip-172-31-25-27.ap-southeast-1.compute.internal",
                    "amiLaunchIndex": 0,
                    "productCodes": {},
                    "instanceType": "t3.medium",
                    "launchTime": 1698825757000,
                    "placement": {
                        "availabilityZone": "ap-southeast-1b",
                        "tenancy": "default"
                    },
                    "monitoring": {
                        "state": "disabled"
                    },
                    "subnetId": "subnet-08f460ce5d424d980",
                    "vpcId": "vpc-0af578573faa8f10d",
                    "privateIpAddress": "172.31.25.27",
                    "stateReason": {
                        "code": "pending",
                        "message": "pending"
                    },
                    "architecture": "x86_64",
                    "rootDeviceType": "ebs",
                    "rootDeviceName": "/dev/xvda",
                    "blockDeviceMapping": {},
                    "virtualizationType": "hvm",
                    "hypervisor": "xen",
                    "tagSet": {
                        "items": [
                            {
                                "key": "aws:ec2launchtemplate:id",
                                "value": "lt-06859e733591a6c06"
                            },
                            {
                                "key": "k8s.io/cluster-autoscaler/enabled",
                                "value": "true"
                            },
                            {
                                "key": "aws:ec2launchtemplate:version",
                                "value": "1"
                            },
                            {
                                "key": "eks:cluster-name",
                                "value": "test"
                            },
                            {
                                "key": "eks:nodegroup-name",
                                "value": "test2"
                            },
                            {
                                "key": "kubernetes.io/cluster/test",
                                "value": "owned"
                            },
                            {
                                "key": "aws:autoscaling:groupName",
                                "value": "eks-test2-06c5c4f3-8ec0-78ca-429c-84bcfac2302e"
                            },
                            {
                                "key": "aws:ec2:fleet-id",
                                "value": "fleet-1fb4718e-e78e-4e3e-0c18-ad80e56dbf97"
                            },
                            {
                                "key": "k8s.io/cluster-autoscaler/test",
                                "value": "owned"
                            }
                        ]
                    },
                    "clientToken": "fleet-1fb4718e-e78e-4e3e-0c18-ad80e56dbf97-0",
                    "groupSet": {
                        "items": [
                            {
                                "groupId": "sg-0ff0e5bdc06c913d5",
                                "groupName": "eks-cluster-sg-test-3556498"
                            }
                        ]
                    },
                    "sourceDestCheck": true,
                    "networkInterfaceSet": {
                        "items": [
                            {
                                "networkInterfaceId": "eni-0b81851d495d06d0a",
                                "subnetId": "subnet-08f460ce5d424d980",
                                "vpcId": "vpc-0af578573faa8f10d",
                                "ownerId": "460453255610",
                                "status": "in-use",
                                "macAddress": "02:fe:e7:54:05:be",
                                "privateIpAddress": "172.31.25.27",
                                "privateDnsName": "ip-172-31-25-27.ap-southeast-1.compute.internal",
                                "sourceDestCheck": true,
                                "interfaceType": "interface",
                                "groupSet": {
                                    "items": [
                                        {
                                            "groupId": "sg-0ff0e5bdc06c913d5",
                                            "groupName": "eks-cluster-sg-test-3556498"
                                        }
                                    ]
                                },
                                "attachment": {
                                    "attachmentId": "eni-attach-03dd221322f03e003",
                                    "deviceIndex": 0,
                                    "networkCardIndex": 0,
                                    "status": "attaching",
                                    "attachTime": 1698825757000,
                                    "deleteOnTermination": true
                                },
                                "privateIpAddressesSet": {
                                    "item": [
                                        {
                                            "privateIpAddress": "172.31.25.27",
                                            "privateDnsName": "ip-172-31-25-27.ap-southeast-1.compute.internal",
                                            "primary": true
                                        }
                                    ]
                                },
                                "ipv6AddressesSet": {},
                                "tagSet": {}
                            }
                        ]
                    },
                    "iamInstanceProfile": {
                        "arn": "arn:aws:iam::460453255610:instance-profile/eks-06c5c4f3-8ec0-78ca-429c-84bcfac2302e",
                        "id": "AIPAWWNJHDG5LVQII6SAQ"
                    },
                    "ebsOptimized": false,
                    "enaSupport": true,
                    "cpuOptions": {
                        "coreCount": 1,
                        "threadsPerCore": 2
                    },
                    "capacityReservationSpecification": {
                        "capacityReservationPreference": "open"
                    },
                    "enclaveOptions": {
                        "enabled": false
                    },
                    "metadataOptions": {
                        "state": "pending",
                        "httpTokens": "optional",
                        "httpPutResponseHopLimit": 2,
                        "httpEndpoint": "enabled",
                        "httpProtocolIpv4": "enabled",
                        "httpProtocolIpv6": "disabled",
                        "instanceMetadataTags": "disabled"
                    },
                    "maintenanceOptions": {
                        "autoRecovery": "default"
                    },
                    "privateDnsNameOptions": {
                        "hostnameType": "ip-name",
                        "enableResourceNameDnsARecord": false,
                        "enableResourceNameDnsAAAARecord": false
                    }
                }
            ]
        },
        "requesterId": "434902558031"
    },
    "requestID": "7c5d5def-467d-426a-ba36-93df8499dda8",
    "eventID": "bc3872b3-cd3d-40ae-bb4b-1ae2b38e4b17",
    "readOnly": false,
    "eventType": "AwsApiCall",
    "managementEvent": true,
    "recipientAccountId": "460453255610",
    "eventCategory": "Management"
}
```

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

