(function( $, undefined ) {

    $.widget( "ui.progressbar", {
	version: "@VERSION",
	options: {
	    max: 100,
	    value: 0,

	    change: null,
	    complete: null
	},

	min: 0,

	_create: function() {
	    // Constrain initial value
	    this.oldValue = this.options.value = this._constrainedValue();

	    this.element
		.addClass("progress")
		.css({'height':'20px', 'width':'200px', 'text-align': 'center'})
		.attr({
		    // Only set static values, aria-valuenow and aria-valuemax are
		    // set inside _refreshValue()
		    role: "progressbar",
		    "aria-valuemin": this.min
		});

	    this.valueDiv = $( "<div class='bar'></div>" )
		.appendTo( this.element );
	    this.valueSpan = $("<span></span>")
		.appendTo( this.valueDiv );

	    this._refreshValue();
	},

	_destroy: function() {
	    this.element
		.removeClass( "progress" )
		.removeAttr( "role" )
		.removeAttr( "aria-valuemin" )
		.removeAttr( "aria-valuemax" )
		.removeAttr( "aria-valuenow" );

	    this.valueDiv.remove();
	},

	value: function( newValue ) {
	    if ( newValue === undefined ) {
		return this.options.value;
	    }

	    this.options.value = this._constrainedValue( newValue );
	    this._refreshValue();
	},

	_constrainedValue: function( newValue ) {
	    if ( newValue === undefined ) {
		newValue = this.options.value;
	    }

	    this.indeterminate = newValue === false;

	    // sanitize value
	    if ( typeof newValue !== "number" ) {
		newValue = 0;
	    }

	    return this.indeterminate ? false :
		Math.min( this.options.max, Math.max( this.min, newValue ) );
	},

	_setOptions: function( options ) {
	    // Ensure "value" option is set after other values (like max)
	    var value = options.value;
	    delete options.value;

	    this._super( options );

	    this.options.value = this._constrainedValue( value );
	    this._refreshValue();
	},

	_setOption: function( key, value ) {
	    if ( key === "max" ) {
		// Don't allow a max less than min
		value = Math.max( this.min, value );
	    }

	    this._super( key, value );
	},

	_percentage: function() {
	    return this.indeterminate ? 100 : 100 * ( this.options.value - this.min ) / ( this.options.max - this.min );
	},

	_refreshValue: function() {
	    var value = this.options.value,
	    percentage = this._percentage();

	    this.valueDiv
		.toggle( this.indeterminate || value > this.min )
		.toggleClass( "ui-corner-right", value === this.options.max )
		.width( percentage.toFixed(0) + "%" );
	    this.valueSpan.html( percentage.toFixed(0) + "%" );
	    if ( this.indeterminate ) {
		this.element.removeAttr( "aria-valuenow" );
	    } else {
		this.element.attr({
		    "aria-valuemax": this.options.max,
		    "aria-valuenow": value
		});
		if ( this.overlayDiv ) {
		    this.overlayDiv.remove();
		    this.overlayDiv = null;
		}
	    }

	    if ( this.oldValue !== value ) {
		this.oldValue = value;
		this._trigger( "change" );
	    }
	    if ( value === this.options.max ) {
		this._trigger( "complete" );
	    }
	}
    });

})( jQuery );