<?php

$target_url = 
$filepath = "/home/pkeane/eris1.jpg";

$file_to_upload = array('file_contents'=>'@'.$filepath);
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL,$target_url);
curl_setopt($ch, CURLOPT_POST,1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $file_to_upload);
$result=curl_exec ($ch);
curl_close ($ch);
echo $result;
?> 

