		<!--

		if (document.images) 
		{   
			var namodn_off = new Image()
			namodn_off.src = "images/namodn_off.png"
			var namodn_on = new Image()
			namodn_on.src = "images/namodn_on.png"

			var onlinegallery_off = new Image()
			onlinegallery_off.src = "images/onlinegallery_off.png"
			var onlinegallery_on = new Image()
			onlinegallery_on.src = "images/onlinegallery_on.png"

			var consulting_off = new Image()
			consulting_off.src = "images/consulting_off.png"
			var consulting_on = new Image()
			consulting_on.src = "images/consulting_on.png"

			var webhosting_off = new Image()
			webhosting_off.src = "images/webhosting_off.png"
			var webhosting_on = new Image()
			webhosting_on.src = "images/webhosting_on.png"

			var community_off = new Image()
			community_off.src = "images/community_off.png"
			var community_on = new Image()
			community_on.src = "images/community_on.png"

			var links_off = new Image()
			links_off.src = "images/links_off.png"
			var links_on = new Image()
			links_on.src = "images/links_on.png"
		}

		function offnow(imgName)
		{     
			if (document.images)
			 document[imgName].src = eval(imgName + '_off.src')
		}

		function onnow(imgName)
		{   
			if (document.images)
			 document[imgName].src = eval(imgName + '_on.src')
		}

		function off(imgName)
		{ 
			if ( SELECTED != imgName )
				offnow(imgName)
		}

		function on(imgName)
		{   
			if (document.images)
			 document[imgName].src = eval(imgName + '_on.src')
		}

		function select(imgName)
		{
			offnow(SELECTED);
			SELECTED = imgName;
		}

		var SELECTED = 'namodn'

		// -->
