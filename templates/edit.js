var images;

if ($('#photo_data').attr('data-some') == "") {
	images = [];
} else {
	images = $('#photo_data').attr('data-some');
}

$('#uploadfile').on('change', handle_upload_button);
$('#post').on('click', function(event) {
	event.preventDefault();
	post_stuff();
});

function handle_upload_button(evt) {
	if(window.File && window.FileReader && window.FileList) {
		var files = evt.target.files;
		console.log(evt.target.files);

		var output = [];
		for (var i=0, f; f = files[i]; i++) {
			if (!f.type.match('image.*')) {
				console.log('file type not supported');
				continue;
			}

			var reader = new FileReader();

			reader.onload = (function(theFile) {
				return function(e) {
					var count = 0;
					var span = document.createElement('span');
					span.innerHTML = ['<img class="thumb" src="', e.target.result, '" title="', escape(theFile.name), '">'].join('');
					$('#thumbs').append(span);	
					upload_file_to_server(e.target.result, count);
				};
			})(f);

			reader.readAsDataURL(f);
		}

	} else {
		console.log("File APIs not supported.");
		return false;
	}
}


function upload_file_to_server(a_file, order) {
	var username = "{{username|safe}}";
	var listing = "{{listing_id|safe}}";
	$.ajax({
		method: 'POST',
		url: '/api/upload_pic',
		data: {
			file: a_file,
			order: order,
			username: username,
			listing: listing
		},
		success: function(resp) {
			var img_url = $.parseJSON(resp).img_url;
			console.log(img_url);
			images.push(img_url);
		}
	});
}


function post_stuff() {
	if (!validate_fields()) {
		return false;
	}
	var title = $('#title').val();
	var price = $('#price').val();
	var incl = $('#incl').val();
	var cond = $('#condition').val();
	var about = $('#about').val();
	var delivery = $('#delivery').val();
	var questions = $('#questions').val();
	var photos = JSON.stringify(images);
	var obj_id = "{{listing_id|safe}}";

	$.ajax({
		type: 'POST',
		url: '/api/post',
		data: {
			title: title,
			price: price,
			incl: incl,
			cond: cond,
			about: about,
			delivery: delivery,
			question: questions,
			photos: photos,
			obj_id: obj_id
		},
		dataType: 'json',
		success: function(resp) {
			if (resp.listing_url) {
				console.log(resp.listing_url);
				window.location.href = resp.listing_url;
				return;
			}
			else {
				alert("Listing posted!");
			}
		},
		beforeSend: function() {
			$('#post').hide();
			return true;
		}
	});

	return false;
}

function validate_fields() {
	var title = $('#title').val();
	if (title.length < 10) {
		alert("Title is too short");
		return false;
	}
	var price = $('#price').val();
	if (price == '') {
		alert("Please set a price");
		return false;
	}
	var cond = $('#condition').val();
	if (cond.length < 2) {
		alert("Please add more details about condition of item");
		return false;
	}

	var incl = $('#incl').val();
	if (incl.length < 10) {
		alert("What's included section is too short");
		return false;
	}
	
	var about = $('#about').val();
	if (about.length < 140) {
		alert("About section needs more information");
		return false;
	}
	var delivery = $('#delivery').val();
	if (delivery.length < 10) {
		alert("Delivery section needs more information");
		return false;
	}
	var questions = $('#questions').val();
	if (questions.length < 10) {
		alert("Please specify the best way to contact you under Further Questions");
		return false;
	}
	if (images.length == 0) {
		alert("Please add at least one photo of the item");
		return false;
	}
	var photos = JSON.stringify(images);
	return true;
}


$('#title, #price, #incl, #condition, #about, #delivery, #questions').keydown(function(e) {
	id = this;
	check_chars(id, e);
});

function check_chars(id, e) {
	allowed_keys = [8, 16, 17, 18, 20, 27, 33, 34, 35, 36, 37, 38, 39, 40, 45, 46];

	// TODO: allow ctrl+a
	id = $(id).attr('id');		

	if (allowed_keys.indexOf(e.which) == -1 && $('#'+id).val().length > get_max(id)) {
		e.preventDefault();
	}
}


$('#title, #price, #incl, #condition, #about, #delivery, #questions').on('paste', function() {
	var el = this;
	//http://stackoverflow.com/questions/686995/jquery-catch-paste-input
	el_id = $(el).attr('id');
	setTimeout(function() {
		var text = removeTags($(el).val()).substring(0, get_max(el_id));
		$(el).html(text);
	}, 100);
});

// http://stackoverflow.com/questions/295566/sanitize-rewrite-html-on-the-client-side
function removeTags(html) {
	var tagBody = '(?:[^"\'>]|"[^"]*"|\'[^\']*\')*';

	var tagOrComment = new RegExp('<(?:'
	    // Comment body.
	    + '!--(?:(?:-*[^->])*--+|-?)'
	    // Special "raw text" elements whose content should be elided.
	    + '|script\\b' + tagBody + '>[\\s\\S]*?</script\\s*'
	    + '|style\\b' + tagBody + '>[\\s\\S]*?</style\\s*'
	    // Regular name
	    + '|/?[a-z]'
	    + tagBody
	    + ')>',
	    'gi');
	  var oldHtml;
  	do {
    	oldHtml = html;
    	html = html.replace(tagOrComment, '');
  	} while (html !== oldHtml);
  	return html.replace(/</g, '&lt;');
}

function get_max(el_id) {
	element_max = {
		"TITLE": 50,
		"PRICE": 10,
		"INCL": 200,
		"COND": 200,
		"ABT": 5000,
		"DEL": 5000,
		"QUES": 2000
	}
	var max = 0;
	switch(el_id)
	{
		case 'title': 
			max = element_max.TITLE;
			break;
		case 'price':
			max = element_max.PRICE;
			break;
		case 'incl':
			max = element_max.INCL;
			break;
		case 'condition':
			max = element_max.COND;
			break;
		case 'about':
			max = element_max.ABT;
			break;
		case 'delivery':
			max = element_max.DEL;
			break;
		case 'questions':
			max = element_max.QUES;
			break; 
	}
	return max;
}



/*
// http://stackoverflow.com/questions/6023307/dealing-with-line-breaks-on-contenteditable-div


$editables = $('[contenteditable=true]');

$editables.filter("p,span").on('keypress',function(e){
 if(e.keyCode==13){ //enter && shift

  e.preventDefault(); //Prevent default browser behavior
  if (window.getSelection) {
      var selection = window.getSelection(),
          range = selection.getRangeAt(0),
          br = document.createElement("br"),
          textNode = document.createTextNode("\u00a0"); //Passing " " directly will not end up being shown correctly
      range.deleteContents();//required or not?
      range.insertNode(br);
      range.collapse(false);
      range.insertNode(textNode);
      range.selectNodeContents(textNode);

      selection.removeAllRanges();
      selection.addRange(range);
      return false;
  }

   }
}); */