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
