transitionEnd = 'transitionend webkitTransitionEnd oTransitionEnd ' +
                'otransitionend MSTransitionEnd'

window.smartfields =
    isCsrfAjaxSetup: false
    alert: bootbox?.alert or alert
    
    getFunction: (func, parent=window) ->
        if not func?
            null
        else if typeof func is 'function'
            func
        else if typeof func is 'string'
            cur_obj = parent
            hierarchy = func.split('.')
            last = hierarchy.length - 1;
            for name in hierarchy
                if !cur_obj?
                    return cur_obj
                cur_obj = cur_obj[name]
            if not typeof cur_obj is 'function'
                throw TypeError("#{func} is not a function")
            cur_obj
        else
            throw TypeError("#{typeof func} is incorrect. Has to be a string or function")

    isSafeMethod: (method) ->
        /^(GET|HEAD|OPTIONS|TRACE)$/.test(method)

    getCookie: (name) ->
        cookieValue = null
        if document.cookie and document.cookie != ''
            cookies = document.cookie.split(';')
            for cookie in cookies
                cookie = $.trim(cookie)
                if cookie.substring(0, name.length + 1) == (name + '=')
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                    break
        cookieValue

    getCsrfToken: (field, csrfCookieName) ->
        # try to get csrftoken from the field, fallback to getting it from a cookie
        csrftoken = field.val()
        if not csrftoken? and csrfCookieName
            csrftoken = @getCookie(csrfCookieName)
        return csrftoken
        
    csrfAjaxSetup: (csrftoken) ->
        if !@isCsrfAjaxSetup
            $.ajaxSetup(
                beforeSend: (xhr, settings) ->
                    if not smartfields.isSafeMethod(settings.type) and not @crossDomain
                        xhr.setRequestHeader("X-CSRFToken", csrftoken)
            )
            @isCsrfAjaxSetup = true

class smartfields.FileField
    constructor: (@$elem) ->
        @$form = @$elem.closest('form')
        @$browseBtn = @$elem.find('.smartfields-btn-browse')
        csrftoken = smartfields.getCsrfToken(
            @$form.find("input[name='csrfmiddlewaretoken']"),
            @$browseBtn.data('csrfCookieName'))
        smartfields.csrfAjaxSetup(csrftoken)
        @id = @$browseBtn.attr('id')
        @$deleteBtn = $("##{@id}_delete")
        @deleting = false
        @$uploadBtn = $("##{@id}_upload")
        @$progress = $("##{@id}_progress").hide()
        @$current = $("##{@id}_current")
        @$errors = $("##{@id}_errors_extra")
        @callbacks =
            onError: smartfields.getFunction(@$browseBtn.data('onError'))
            onComplete: smartfields.getFunction(@$browseBtn.data('onComplete'))
            onReady: smartfields.getFunction(@$browseBtn.data('onReady'))
            onBusy: smartfields.getFunction(@$browseBtn.data('onBusy'))
            onProgress: smartfields.getFunction(@$browseBtn.data('onProgress'))

        @$browseBtn.change( =>
            # in case plupload fails to inititalize
            file_name = @$browseBtn.val().split('\\').pop() # remove 'fakepath'
            @$current.val(file_name)
        )
        @$currentBtn = $("##{@id}_link").click ->
            href = $(@).data('href')
            if href
                window.open(href, $(@).data('target')).focus()
        @$uploadBtn.hide()
        if !@$current.val()
            @$deleteBtn.hide()
            @$currentBtn.parent().hide()
        @$deleteBtn.click =>
            if @deleting
                return false
            @deleting = true
            $.ajax(@options.url, type: 'DELETE', success: (data, textStatus, jqXHR) =>
                if data.state == 'complete'
                    @$current.val('')
                    @$currentBtn.data('href', "").hide()
                    @$deleteBtn.hide()
                    @fileDeleted(data, textStatus, jqXHR)
                else
                    extra = ""
                    if data.task_name
                        extra = " , it is #{data.task_name}"
                    smartfields.alert(
                        "Cannot delete this file right now#{extra}. Please try again later.")
                @deleting = false
            )
        @options = {
            browse_button: @id,
            container: @$elem[0],
            file_data_name: @$browseBtn.attr('name'),
            init: {
                Init:           $.proxy(@Init, @),
                PostInit:       $.proxy(@PostInit, @),
                OptionChanged:  $.proxy(@OptionChanged, @),
                Refresh:        $.proxy(@Refresh, @),
                StateChanged:   $.proxy(@StateChanged, @),
                UploadFile:     $.proxy(@UploadFile, @),
                BeforeUpload:   $.proxy(@BeforeUpload, @),
                QueueChanged:   $.proxy(@QueueChanged, @),
                UploadProgress: $.proxy(@UploadProgress, @),
                FilesRemoved:   $.proxy(@FilesRemoved, @),
                FileFiltered:   $.proxy(@FileFiltered, @),
                FilesAdded:     $.proxy(@FilesAdded, @),
                FileUploaded:   $.proxy(@FileUploaded, @),
                ChunkUploaded:  $.proxy(@ChunkUploaded, @),
                UploadComplete: $.proxy(@UploadComplete, @),
                Error:          $.proxy(@Error, @),
                Destroy:        $.proxy(@Destroy, @)
            }
        }
        if csrftoken
            @options.headers = 'X-CSRFToken': csrftoken
        $.extend(@options, @$browseBtn.data('pluploadOptions'))
        @uploader = new plupload.Uploader(@options)
        @uploader.init()
        @counterName = 'smartfieldsUploadCounter'
        @formSubmitted = false
        @$form.submit =>
            if @uploader.files.length > 0 and @uploader.state is plupload.STOPPED
                @uploader.start()
            if not @formSubmitted and @uploader.state is plupload.STARTED
                @$form.data(@counterName, (@$form.data(@counterName) or 0) + 1)
                @formSubmitted = true
                if not @$browseBtn.data('silent') and @$form.data(@counterName) is 1
                    smartfields.alert("This form contains a file(s) that can take some time 
                        to upload. Please, wait for it to finish, you should be able to see 
                        the progress under the file input. It will proceed automatically 
                        once it's done uploading.")
            @uploader.state is plupload.STOPPED and not @$form.data(@counterName)


    setProgress: (index, percent, task_name) ->
        if !index? && !percent? && !task_name?
            for bar in @$progress.children()
                $(bar).attr('aria-valuenow', 0)
                    .width("0%")
                    .find('span').html("Ready")
        else
            len = @$progress.children().length
            if index > 0
                bar = @$progress.children()[len - index]
                $(bar).attr('aria-valuenow', 100-percent)
                    .width("#{100-percent}%")
            bar = @$progress.children()[len - 1 - index]
            $(bar).attr('aria-valuenow', percent)
                .width("#{percent}%")
                .find('span').html("#{percent}% #{task_name}")
            @$current.val("#{task_name}... #{percent}%")


    handleResponse: (data, complete, error) ->
        submitForm = (state) =>
            if @formSubmitted and state isnt 'error'
                @$form.data(@counterName, (@$form.data(@counterName) or 1) - 1)
                if @$form.data(@counterName) is 0
                    @$form.submit()
        if data.state is 'complete'
            completed = false
            delayedComplete = () =>
                if not completed
                    completed = true
                    @$progress.hide()
                    @setProgress()
                    @$deleteBtn.show()
                    @$current.val(data.file_name)
                    @$currentBtn.data('href', data.file_url).parent().show()
                    complete?(data)
                    @callbacks.onComplete?(@, data)
                    submitForm(data.state)
            @setProgress(1, 100, data.task_name)
            @$progress.one(transitionEnd, => delayedComplete)
            #transitionEnd is not guaranteed to fire. setTimeout as a fallback
            setTimeout(delayedComplete, 1500)
        else if data.state is 'error'
            @setErrors(data.messages)
            error?(data)
            @callbacks.onError?(@, data)
        else if data.state != 'ready'
            if data.state is 'in_progress'
                progress = Math.round(100 * data.progress)
                @setProgress(1, progress, data.task_name)
                @callbacks.onProgress?(@, data, progress)
                submitForm(data.state)
            setTimeout((=> $.get(@options.url, (data) => @handleResponse(data))), 3000)
        else if data.state is 'ready'
            @callbacks.onReady?(@, data)

            

    fileDeleted: (data, textStatus, jqXHR) ->

    setErrors: (errors) ->
        @$errors.empty()
        if errors
            @$progress.hide()
            @setProgress()
            @$elem.addClass('has-error')
            @$current.val("ERROR")
            for e, i in errors
                @$errors.append($("<li>",
                    'id': "error_#{i}_#{@id}",
                    'class': "bg-danger"
                ).html($("<strong>").text(e)))
        else
            @$elem.removeClass('has-error')


    # Plupload callbacks below:

    Init: ->

    OptionChanged: ->

    Refresh: ->

    StateChanged: ->

    UploadFile: ->

    QueueChanged: ->

    FilesRemoved: (up, file) ->

    FileFiltered: (up, file) ->

    ChunkUploaded: ->

    UploadComplete: ->

    Error: (up, error) ->
        switch error.code
            when plupload.FILE_EXTENSION_ERROR
                @setErrors(["Unsupported file type: #{error.file.name}"])
                up.splice(0, up.files.length) # remove unsupported file
            when plupload.FILE_SIZE_ERROR
                size = plupload.formatSize(error.file.size)
                maxSize = @options.filters?.max_file_size
                maxSizeMessage = ""
                if maxSize
                    maxSize = plupload.parseSize(maxSize)
                    maxSize = plupload.formatSize(maxSize)
                    maxSizeMessage = " Maximum size is: #{maxSize}"
                @setErrors(["File is too big: #{size}.#{maxSizeMessage}"])
                up.splice(0, up.files.length) # remove unsupported file
            else @setErrors([error.message])

    Destroy: ->

    PostInit: (up) ->
        @$browseBtn.click( -> false)
            .replaceWith(@$elem.find(".moxie-shim").hide().find('input'))
        @$uploadBtn.click ->
            up.start()
            false
        status = @$browseBtn.data('status')
        if status?.state == 'in_progress'
            @$progress.show()
        @handleResponse(status)

    FilesAdded: (up, files) ->
        @$current.val(files[0].name)
        @$uploadBtn.show()
        @$progress.show()
        @$deleteBtn.hide()
        # remove previously selected files from the queue, so only one left
        up.splice(0, up.files.length-1)
        @setErrors()

    BeforeUpload: ->
        @setProgress()
        @$uploadBtn.hide()

    UploadProgress: (up, file) ->
        @setProgress(0, file.percent, "Uploading")

    FileUploaded: (up, file, data) ->
        up.removeFile(file)
        if data.status == 200
            response = $.parseJSON(data.response)
            @handleResponse(response)
        else if data.status == 409
            response = $.parseJSON(data.response)



class smartfields.MediaField extends smartfields.FileField
    constructor: ($elem) ->
        super $elem
        @$currentPreview = $("##{@id}_preview")

    fileDeleted: (data, textStatus, jqXHR) ->
        @$currentPreview.empty()

    handleResponse: (data, complete, error) ->
        super data, ((data) =>
            $preview = @$currentPreview.empty()
                .removeClass('smartfields-loading')
                .html(data.html_tag)
            # make sure server is ready to serve the file, by retrying the load
            persistentLoader = (attempts) =>
                @$currentPreview.find("[src]").each( ->
                    $(@).load(->)
                    .error(->
                        if attempts > 0
                            setTimeout((->
                                $preview.empty().html(data.html_tag)
                                persistentLoader(attempts - 1)
                                ), 1000)
                    )
                )
            persistentLoader(5)
            complete?()
            ), error

    setProgress: (index, percent, task_name) ->
        @$currentPreview.empty().addClass('smartfields-loading')
        super index, percent, task_name
        
    BeforeUpload: ->
        @$currentPreview.empty().addClass('smartfields-loading')
        super

class smartfields.LimitedField
    constructor: (@$elem) ->
        $field = @$elem.find(".smartfield")
        $feedback = @$elem.find(".feedback-counter")
        maxlength = parseInt($field.attr("maxlength") or $field.data("maxlength"))
        if not isNaN maxlength
            $field.keyup ->
                content = $field.val()
                # account for new lines as 2 characters
                newlines = content.split('\n').length - 1
                current_length = content.length + newlines
                if current_length >= maxlength
                    content = content.substr(0, maxlength-newlines)
                    $field.val(content)
                    newlines = content.split('\n').length - 1
                    current_length = content.length + newlines
                $feedback.text(maxlength - current_length)
                true
            .trigger('keyup')


$(document).ready ->
    $(".smartfields-filefield").each ->
        if not $(@).data('smartfield')?
            $(@).data('smartfield', new smartfields.FileField($(@)))
        null

    $(".smartfields-mediafield").each ->
        if not $(@).data('smartfield')?
            $(@).data('smartfield', new smartfields.MediaField($(@)))
        null

    $(".smartfields-limitedfield").each ->
        if not $(@).data('smartfield')?
            $(@).data('smartfield', new smartfields.LimitedField($(@)))
        null
    null
