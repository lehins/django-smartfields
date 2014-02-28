smartfields = {
    setProgress : ($progressbar, percent) ->
        $progressbar.attr('aria-valuenow', percent)
            .css('width', percent + "%")
            .find('span').html(percent + "% Complete")
}

class smartfields.FileField
    constructor: (@$elem) ->
        @$browse_btn = @$elem.find('.smartfields-btn-browse').click -> false
        @id = @$browse_btn.attr('id')
        @$delete_btn = $("##{@id}_delete")
        @$upload_btn = $("##{@id}_upload")
        @$upload_bar = $("##{@id}_progressbar_upload")
        @$server_bar = $("##{@id}_progressbar_server")
        @$current = $("##{@id}_current")
        @$current_link = $("##{@id}_link").click ->
            href = $(@).data('href')
            if href
                window.open(href, '_blank').focus()
        @options = @$browse_btn.data('plupload')
        @$upload_btn.parent().hide()
        @$upload_bar.parent().hide()
        if !@$current.val()
            if @$delete_btn
                @$delete_btn.parent().hide()
            @$current_link.parent().hide()

        defOptions = {
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
        $.extend(@options, defOptions)
        @uploader = new plupload.Uploader(@options)
        @uploader.init()

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
        if @$delete_btn
            @$delete_btn.click =>
                post_data = {
                    'csrfmiddlewaretoken': @$browse_btn.data('csrfToken')
                }
                post_data["#{@$browse_btn.attr('name')}-clear"] = "on"
                $.post(@options.url, post_data, (data, textStatus, jqXHR) =>
                    if data.status == 'complete'
                        @$current.val('')
                        @$current_link.attr('href', "").parent().hide()
                        @$delete_btn.parent().hide()
                        @postDeleteCallback(data, textStatus, jqXHR)
                )

    FilesAdded: (up, files) ->
        @$current.val(files[0].name)
        @$upload_btn.parent().show()
        @$upload_bar.parent().show()
        if @$delete_btn then @$delete_btn.parent().hide()
        # remove previously selected files from the queue, so only one left
        up.splice(0, up.files.length-1)

    BeforeUpload: ->
        @$upload_btn.parent().hide()

    UploadProgress: (up, file) ->
        smartfields.setProgress(@$upload_bar, file.percent)

    FileUploaded: (up, file, data) ->
        if data.status == 200
            response = $.parseJSON(data.response)
            if response.status == 'complete'
                if @$delete_btn then @$delete_btn.parent().show()
                @$upload_bar.one('transitionend webkitTransitionEnd oTransitionEnd ' +
                    'otransitionend MSTransitionEnd', =>
                        smartfields.setProgress(@$upload_bar, 0)
                        @$upload_bar.parent().hide()
                )
                @$current.val(response.file_name)
                @$current_link.attr('href', response.file_url).parent().show()


class smartfields.ImageField extends smartfields.FileField
    constructor: (@$elem) ->
        super @$elem
        @$current_preview = $("##{@id}_preview")

    postDeleteCallback: (data, textStatus, jqXHR) ->
        if data.status == 'complete'
            @$current_preview.attr('src', '')


    FileUploaded: (up, file, data) ->
        if data.status == 200
            response = $.parseJSON(data.response)
            if response.status == 'complete'
                @$current_preview.attr('src', response.file_url)
        super up, file, data

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
