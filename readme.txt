
测试环境

OS : Linux Mint 21.2 x86_64
Kernel : 5.15.0-79-generic
CPU : AMD Ryzen Embedded V1605B
GPU : AMD ATI Radeon Vega
Memory : 16GB
Storage : 256GB SSD
Python : 3.10.12

注意事项

在运行程序之前，请先把config和credentials两个文件放在~/.aws目录下
确保在程序文件prj1.py的同目录下存在CSE546test.txt文件
确保prj1.py有权限对当前目录有写权限（下载CSE546test.txt到本地）
另，huizhili_key_pair.pem为本人账户的密钥对文件，当使用ssh连接ec2时需要此文件，具体命令如下：
chmod 400 huizhili_key_pair
ssh -i huizhili_key_pair.pem ec2-user@ec2-35-171-155-199.compute-1.amazonaws.com
注意，实际运行时请将ec2-35-171-155-199.compute-1.amazonaws.com替换成实际的实例地址


python3 workload_generator.py \
 --num_request 3 \
 --url 'http://localhost:8080' \
 --image_folder "your_local_image_folder"


while true:

	sleep(5)

	check messages in sqs_input queue
	check messages in sqs_output queue
	check running instance count with tag

	if (msg_count_in_sqs_input == 0 && msg_count_in_sqs_output == 0)
	{
		stop all the instances
	}
	
	if (msg_count_in_sqs > 0)
	{
		if (running_count_instances + pending_count_instances > 20 )	
			do nothing

		if (running_count_instances + pending_count_instances == 0 )	
			start instances

		if (running_count_instances + pending_count_instances => 10 && running_count_instances + pending_count_instances <= 20)	
		    start msg_count_in_sqs // 10
			
	}

