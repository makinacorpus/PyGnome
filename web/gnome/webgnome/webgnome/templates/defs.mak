### Mako defs.

<%def name="is_active(url)">
    % if request.path == url:
        active
    % endif
</%def>

<%def name="form_control(field, help_text=None)">
    <div class="control-group ${ 'error' if field.errors else ''}">
        <label class="control-label">${ field.label.text }</label>

        <div class="controls">
            ${ field }
            % if field.errors:
                <span class="help-inline">
                    %for error in field.errors:
                        ${ error }
                    %endfor
                </span>
            % endif
            % if help_text:
                <span class="help-inline">${ help_text }</span>
            % endif
        </div>
    </div>
</%def>

