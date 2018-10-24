function request()
{
	var req = new XMLHttpRequest();
	req.onreadystatechange = function()
	{
		if(req.readyState == 4 && req.status == 200)
		{
			var json = JSON.parse(req.responseText);
			console.log(json);
			json.forEach(data =>
			{
				element = document.getElementById(data['release_channel']);
				element.getElementsByClassName('build_number')[0].textContent = data['build_number'];
				element.getElementsByClassName('version_hash')[0].textContent = data['version_hash'];
			});
		}
	};
	req.open("GET", "api/all.json", true);
	req.send();
}

window.onload = request();
