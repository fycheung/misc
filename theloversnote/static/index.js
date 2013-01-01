// JavaScript Document
var xmlhttp;
function getXmlHttp(){
	var xmlhttp;
	if (window.XMLHttpRequest)
	  {// code for IE7+, Firefox, Chrome, Opera, Safari
	  xmlhttp=new XMLHttpRequest();
	  }
	else
	  {// code for IE6, IE5
	  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
	  }
	  return xmlhttp;
}
function getCode(){
	var code = document.getElementById("code").value
	var type = document.getElementById("type").value
	if(code == null||code.length ==0){alert("please input your code!"); return;}
	if(type == null){alert("please choose one type!!"); return;}
	xmlhttp = getXmlHttp();
	xmlhttp.onreadystatechange=showCode;
	xmlhttp.open("GET","/code",true);
	xmlhttp.send();
}
function showCode()
  {
  if (xmlhttp.readyState==4 && xmlhttp.status==200)
    {
    document.getElementById("show").innerHTML=xmlhttp.responseText;
    }
  }