function request()
{
	["stable", "ptb", "canary"].forEach(channel => {
		let req = new XMLHttpRequest();
		req.onreadystatechange = function()
		{
			if(req.readyState == 4 && req.status == 200)
			{
				var json = JSON.parse(req.responseText);
				console.log(json);
				element = document.getElementById(json['release_channel']);
				element.getElementsByClassName('build_number')[0].textContent = json['build_number'];
				element.getElementsByClassName('version_hash')[0].textContent = json['version_hash'];
			}
		};
		req.open("GET", `api/${channel}.json`, true);
		req.send();
	});
}

window.onload = request();
