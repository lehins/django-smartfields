var smartfields = {

    VERSION: '0.0.2',

    init: function(){
	$('.sf-limit-length').each(function(i, elem){
	    var $this = $(elem);
	    var maxlength = parseInt($this.data("maxlength"));
	    var minlength = parseInt($this.data("minlength"));
	    if(isNaN(minlength) && isNaN(maxlength)){
		return;
	    }
	    var text = "Text length has to be ";
	    var count_elem = $("<span>").text($this.val().length);
	    if(!isNaN(minlength)){
		text = text + "at least " + minlength;
	    }
	    if(!isNaN(maxlength)){
		text = text + "at most " + maxlength;
		$this.keyup(function(){
		    var content = $this.val();
		    if(content.length > maxlength){
		    content = content.substr(0, maxlength);
		    $this.val(content);
		}
		count_elem.text(content.length);
	    });
	    }
	    text+= " characters. Current length is: ";
	    $this.before($("<div>").text(text).append(count_elem));
	});
    },
    get_err_msg: function(err, settings){
	var file = err.file;
	if (file && err.code == plupload.FILE_SIZE_ERROR) {
	    return "Files over " + settings.max_file_size + 
		" are not allowed. " + file.name + " is too large.";
	}

	if (file && err.code == plupload.FILE_EXTENSION_ERROR) {
	    var list = file.name.split('.'), ext = "", message = "";
	    if(settings.filters && settings.filters.length){
		var filters = [];
		$.each(settings.filters, function(i, filter){
		    filters.push.apply(
			filters, filter.extensions.split(','));
		});
		var ext_msg = filters.length > 1 ? "extensions" : "extension";
		message = "Only files with '" + filters + 
		    "' " + ext_msg + " are allowed. ";
	    }
	    message+= "'" + file.name + 
		"' can not be uploaded.";
	    return message;
	}
	return null;
    },

    DjangoUploader: function(name, remove_btn_id, settings){
	var freq = 1000;
	var file_elem = null;
	var file_elem_container = $("#" + name + "_container");
	var progress_bar = null;
	var progress_text = $('<strong>');
	var browse_btn = $("#" + name + "_browse_btn");
	var upload_btn = $("#" + name + "_upload_btn");

	var remove_remote_btn = $("#" + remove_btn_id);
	var initial_container = $("#" + name + "_initial");
	var errors_container = $("<div>", {'class': "errorlist"});
	var csrf_token = settings.multipart_params.csrfmiddlewaretoken;
	var uploader = new plupload.Uploader(settings);
	remove_remote_btn.click(function(){
	    var post_data = {'csrfmiddlewaretoken': csrf_token};
	    post_data[remove_remote_btn.attr('name')] = 'on'; 
	    $.post(
		uploader.settings.url, 
		post_data,
		function(data){
		    if(data && data.task == 'uploading' && data.status =='complete'){
			initial_container.html(data.rendered_result);
			remove_remote_btn.hide();
		    }
		});
	    return false;
	});

	function update_progress(){
	    $.getJSON(uploader.settings.url, function(data, status){
		if(data && data.task == 'converting'){
		    window.setTimeout(update_progress, freq);
		    var progress = Math.round(data.progress);
		    progress_bar.progressbar("option", "value", progress);
		    progress_text.html(data.task_name +": " + progress + "%");
		} else if(data && data.task == 'uploading' && 
			  data.status == 'complete'){
		    file_elem.remove();
		    browse_btn.show();
		    remove_remote_btn.show();
		    initial_container.html(data.rendered_result);
		}
	    });
	}
	uploader.bind('FilesAdded', function(up, files) {
	    for(var i in uploader.files){
		uploader.removeFile(uploader.files[i]);
	    }
	    $.each(files, function(i, file) {
		file_elem = $('<div id="' + file.id + '">' + file.name + ' (' + 
			      plupload.formatSize(file.size) + ') </div>');
		remove_btn = $('<a class="icon-remove" href="" data-file-id="'
			       + file.id + '"></a>');
		progress_text.html(remove_btn);
		progress_bar = $('<div>').progressbar({value: 0})
		    .css({'width': '200px', 'height': '20px'});
		file_elem.append(progress_text).append(progress_bar);
		file_elem_container.append(file_elem);
		progress_bar.hide();
		$(remove_btn).click(function(){
		    var file_id = $(this).data('fileId');
		    uploader.removeFile(uploader.getFile(file_id));
		    return false;
		});
	    });
	    upload_btn.show();
	});
	uploader.init();
	uploader.bind('Error', function(up, err){
	    var message = smartfields.get_err_msg(err, settings);
	    if(!message){
		message = err.message;
	    }
	    if(err.errors){
		message = "";
		$.each(err.errors, function(i, error){
		    message+= "<div class='errorText alert alert-error'>"
			+ error + "</div>";
		});
	    } else {
		message = "<div class='errorText alert alert-error'>" + message +
		    "</div>";
	    }
	    errors_container.html(message);
	    file_elem.html(errors_container);
	    upload_btn.hide();
	    browse_btn.show();
	});

    
	uploader.bind('FilesRemoved', function(up, files) {
	    file_elem.remove();
	    upload_btn.hide();

	});
	uploader.bind('BeforeUpload', function(up, file) {
	    browse_btn.hide();
	    progress_bar.show();
	    remove_remote_btn.hide();
	});
	uploader.bind('UploadProgress', function(up, file) {
	    $(progress_bar).progressbar("option", "value", file.percent);
	    progress_text.html("Uploading: " + file.percent + "%");
	});

	uploader.bind('FileUploaded', function(up, file, response) {
	    if(response.status == '200'){
		var data = $.parseJSON(response.response);
		if(data.task == 'uploading'){
		    if(data.status == 'complete'){
			uploader.removeFile(file);
			initial_container.html(data.rendered_result);
			browse_btn.show();
			remove_remote_btn.show();
		    } else if(data.status == 'failed'){
			uploader.trigger("Error", {
			    file: file,
			    code: plupload.GENERIC_ERROR,
			    errors: data.errors
			});
		    }
		} else if(data.task == 'converting'){
		    window.setTimeout(update_progress, freq);
		}
	    } 
	    
	});
	upload_btn.hide().click(function() {
	    $(this).hide();
	    uploader.start();
	    return false;
	});

    },

    DjangoQueue: function(id, settings, initial_files){
	var queue = $("#" + id);
	var plupload_settings = settings;
	var csrf_token = plupload_settings.multipart_params.csrfmiddlewaretoken;
	var initial_files = initial_files;
	var uploader = null;
	var filelist_container = null;

	function removeRemote(pk){
	    $.post(
		uploader.settings.url, 
		{
		    'task': "delete", 
		    'pk': pk,
		    'csrfmiddlewaretoken': csrf_token
		},
		function(data){
		    if(data && data.task == 'delete'){
			if(data.status =='complete'){
			    for(var j in initial_files){
				if(initial_files[j][0] == data.file_elem_id){
				    initial_files.splice(j, 1);
				    break;
				}
			    }
			    $("#" + data.file_elem_id).remove();
			} else if(data.status == 'failed' && data.errors){
			    alert(data.errors.join('\n'));
			}
		    }
		});
	}

	function addToList(){

	    filelist_container.children().each(function(){
		filelist_container.prepend($(this));
	    });
	    $.each(initial_files, function(i, initial_file){
		var file_elem_id = initial_file[0];
		var file_size = plupload.formatSize(initial_file[1]);
		var file_elem = initial_file[2];
		filelist_container.append(file_elem);
		$("#" + file_elem_id + " > div.plupload_file_size")
		    .html(file_size);
		$("#" + file_elem_id + " > div.plupload_file_action > a").click(
		    function(){
			var conf = confirm(
			    "Are you sure you want to remove '" +
				$("#" + file_elem_id + 
				  " > div.plupload_file_name > span")
				.text() + "' ?");
			if(conf){
			    var pk = $(this).data('pk');
			    removeRemote(pk);
			}
			return false;
		    });
	    });
	    $(".plupload_file_link").click(function(){
		window.open($(this).data('href'));
	    });
	}

	function init(){
	    var uploaded_files = [];
	    queue.pluploadQueue(plupload_settings);
	    uploader = queue.pluploadQueue();
	    filelist_container = $("#" + id + "_filelist");
	    $("#" + id + "_container").attr('title', "");
	    
	    uploader.bind('FilesAdded', function(up, files){
		filelist_container.children().each(function(){
		    $(this).remove();
		});
	    });
	    uploader.bind('FileUploaded', function(up, file, response){
		if(response.status == '200'){
		    var data = $.parseJSON(response.response);
		    if(data.task == 'uploading'){
			if(data.status == 'complete'){
			    uploaded_files.unshift(data.rendered_result);
			} else if(data.status == 'failed'){
			    uploader.trigger("Error",{
				file: file,
				code: plupload.GENERIC_ERROR,
				message: data.errors.join('\n')
			    });
			}
		    }
		}
	    });
	    uploader.bind('QueueChanged', addToList);
	    uploader.bind('UploadComplete', function(up, files){
		addToList();
		queue.find("span.plupload_upload_status").prepend(
		    $('<a href="" class="plupload_button">Upload more...</a>')
			.click(function(){
			    $.each(uploaded_files, function(i, file){
				initial_files.unshift(uploaded_files.pop());
			    });
			    uploader.destroy();
			    delete uploader;
			    queue.children().each(function(){
				$(this).remove();
			    });
			    init();
			    return false;
			})
		);
	    });
	    uploader.unbind("Error");
	    uploader.bind("Error", function(up, err) {
		var file = err.file;
		if (file) {
		    var message = err.message;
		    file.status = plupload.FAILED;
		    
		    if (err.details) {
			message += " (" + err.details + ")";
		    }
		    var err_msg = smartfields.get_err_msg(err, settings);
		    if(err_msg){
			message = err_msg;
			alert(message);
		    }
		    file.hint = message;
		    $('#' + file.id).attr('class', 'plupload_failed')
			.find('a').css('display', 'block').attr('title', message);
		    uploader.trigger("QueueChanged");
		}
	    });
	    if(initial_files.length){
		filelist_container.html('');
		addToList();
	    } 
	}
	init();
    }
};

$(document).ready(smartfields.init);
