transitionEnd = 'transitionend webkitTransitionEnd oTransitionEnd ' +
                'otransitionend MSTransitionEnd'

smartfields = {}

class smartfields.FileField
    constructor: (@$elem) ->
        @$browse_btn = @$elem.find('.smartfields-btn-browse').click -> false
        @id = @$browse_btn.attr('id')
        @$delete_btn = $("##{@id}_delete")
        @$upload_btn = $("##{@id}_upload")
        @$progress = $("##{@id}_progress").hide()
        @$current = $("##{@id}_current")
        @$current_btn = $("##{@id}_link").click ->
            href = $(@).data('href')
            if href
                window.open(href, $(@).data('target')).focus()
        @$upload_btn.parent().hide()
        if !@$current.val()
            @$delete_btn.parent().hide()
            @$current_btn.parent().hide()

        @options = {
            'browse_button': @id,
            'container': @$elem[0],
            'file_data_name': @$browse_btn.attr('name'),
            'multipart_params': {
                'csrfmiddlewaretoken': @$browse_btn.data('csrfToken')
            },
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
                Destroy:        $.proxy(@Destroy @)
            }
        }
        $.extend(@options, @$browse_btn.data('plupload'))
        @uploader = new plupload.Uploader(@options)
        @uploader.init()


    setProgress : (index, percent, task_name) ->
        if !index? && !percent? && !task_name?
            for bar in @$progress.children()
                $(bar).attr('aria-valuenow', 0)
                    .width("0%")
                    .find('span').html("Ready")
        else
            len = @$progress.children().length
            bar = @$progress.children()[len - 1 - index]
            $(bar).attr('aria-valuenow', percent)
                .width("#{percent}%")
                .find('span').html("#{percent}% #{task_name}")
            @$current.val("#{task_name}... #{percent}%")
            if index > 0
                bar = @$progress.children()[len - index]
                $(bar).attr('aria-valuenow', 100-percent)
                    .width("#{100-percent}%")


    handleResponse: (data, complete, error) ->
        if data.state == 'complete'
            completed = false
            delayedComplete = () =>
                if !completed
                    completed = true
                    @$progress.hide()
                    @setProgress()
                    @$delete_btn.parent().show()
                    @$current.val(data.file_name)
                    @$current_btn.data('href', data.file_url).parent().show()
                    complete?(data)
            @setProgress(1, 100, data.task_name)
            @$progress.one(transitionEnd, => delayedComplete)
            setTimeout(delayedComplete, 2000)
        else if data.state == 'error'
            console.log(data)
            error?(data)
        else if data.state != 'ready'
            if data.state == 'in_progress'
                progress = Math.round(100 * data.progress)
                @setProgress(1, progress, data.task_name)
            setTimeout((=> $.get(@options.url, (data) => @handleResponse(data))), 3000)


    postDeleteCallback: (data, textStatus, jqXHR) ->

    Init: ->

    OptionChanged: ->

    Refresh: ->

    StateChanged: ->

    UploadFile: ->

    QueueChanged: ->

    FilesRemoved: ->

    FileFiltered: ->

    ChunkUploaded: ->

    UploadComplete: ->

    Error: ->

    Destroy: ->

    PostInit: (up) ->
        @$browse_btn.replaceWith(@$elem.find(".moxie-shim").hide().find('input'))
        @$upload_btn.click ->
            up.start()
            false
        @$delete_btn.click =>
            post_data = {
                'csrfmiddlewaretoken': @$browse_btn.data('csrfToken')
            }
            post_data["#{@$browse_btn.attr('name')}-clear"] = "on"
            $.post(@options.url, post_data, (data, textStatus, jqXHR) =>
                if data.state == 'ready'
                    @$current.val('')
                    @$current_btn.data('href', "").parent().hide()
                    @$delete_btn.parent().hide()
                    @postDeleteCallback(data, textStatus, jqXHR)
                )
        status = @$browse_btn.data('status')
        if status?.state == 'in_progress'
            @$progress.show()
        @handleResponse(status)

    FilesAdded: (up, files) ->
        @$current.val(files[0].name)
        @$upload_btn.parent().show()
        @$progress.show()
        @$delete_btn?.parent().hide()
        # remove previously selected files from the queue, so only one left
        up.splice(0, up.files.length-1)

    BeforeUpload: ->
        @setProgress()
        @$upload_btn.parent().hide()

    UploadProgress: (up, file) ->
        @setProgress(0, file.percent, "Uploading")

    FileUploaded: (up, file, data) ->
        if data.status == 200
            response = $.parseJSON(data.response)
            @handleResponse(response)
        else if data.status == 409
            response = $.parseJSON(data.response)
            console.log(response)



class smartfields.ImageField extends smartfields.FileField
    constructor: (@$elem) ->
        super @$elem
        @$current_preview = $("##{@id}_preview")

    postDeleteCallback: (data, textStatus, jqXHR) ->
        @$current_preview.empty()

    handleResponse: (data) ->
        super data, (data) => @$current_preview.empty().html(data.html_tag)


class smartfields.LimitedField
    constructor: (@$elem) ->
        $field = @$elem.find(".smartfield")
        $feedback = @$elem.find(".feedback-counter")
        maxlength = parseInt($field.attr("maxlength") or $field.data("maxlength"))
        if not isNaN maxlength
            $field.keyup ->
                content = $field.val()
                # account for new lines as 2 characters
                current_length = content.length + content.split('\n').length - 1
                if current_length > maxlength
                    content = content.substr(0, maxlength)
                    $field.val(content)
                $feedback.text(maxlength - current_length)
                true
            .trigger('keyup')


$(document).ready ->
    $(".smartfields-filefield").each ->
        new smartfields.FileField($(@))
        null

    $(".smartfields-imagefield").each ->
        new smartfields.ImageField($(@))
        null
    null

    $(".smartfields-limitedfield").each ->
        new smartfields.LimitedField($(@))
        null
    null
