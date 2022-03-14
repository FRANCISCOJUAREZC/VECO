odoo.define('invoice_xunnel.document_viewer', (require) => {

    const DocumentsViewer = require('@mail/js/document_viewer')[Symbol.for("default")];
    const ajax = require('web.ajax');
    const { qweb } = require('web.core');

    DocumentsViewer.include({
        xmlDependencies: [
            '/invoice_xunnel/static/src/xml/templates.xml'
        ],
        init(parent, documents, activedocumentID){
            this._super.apply(this, arguments);
            this.document = _.filter(documents, function(document) {
                var match = document.type == 'url' ? document.url.match("(youtu|.png|.jpg|.gif)") : document.mimetype.match("(image|video|application/pdf|text)");
                if (match) {
                    document.type = match[1];
                    if (match[1].match("(.png|.jpg|.gif)")) {
                        document.type = 'image';
                    }
                    if (match[1] === 'youtu') {
                        var youtube_array = document.url.split('/');
                        var youtube_token = youtube_array[youtube_array.length-1];
                        if (youtube_token.indexOf('watch') !== -1) {
                            youtube_token = youtube_token.split('v=')[1];
                            var amp = youtube_token.indexOf('&')
                            if (amp !== -1){
                                youtube_token = youtube_token.substring(0, amp);
                            }
                        }
                        document.youtube = youtube_token;
                    }
                    return true;
                } else{
                    const match = document.type == 'url' ? false : document.mimetype.match("application/xml");
                    if (match) {
                        return true;
                    }
                }
            });
            this.activedocument = _.findWhere(documents, {id: activedocumentID});
            this._reset();
        }, start(){
            this._super.apply(this, arguments);
            this._updateContent();
        }, _updateContent(){
            this._super.apply(this, arguments);
            let xmlViewer = $('.o_viewer_xml').eq(0);
            if(xmlViewer.length){
                const route = xmlViewer.data('src');
                ajax.post(route, {}).then((view) => {
                    const html = qweb.render('invoice_xunnel.xml_preview', { view });
                    xmlViewer.html(PR.prettyPrintOne(html.trim()));
                    xmlViewer.find('pre.prettyprint .atn, pre.prettyprint .atv').click(
                        this.copy_attribute.bind(this))
                });
            }
        }, _onClose(ev){
            const target = $(ev.target);
            if(target.parents('.prettyprint').length || target.hasClass('prettyprint')){
                return true;
            }
            this._super(ev);
        }, copy_attribute(ev){
            ev.preventDefault();
            ev.stopPropagation();
            const target = $(ev.currentTarget);
            const text = target.hasClass('atv')
                ? this.get_target_value(target)
                : this.get_target_value(target.next().next());
            this.copy(text);
        }, get_target_value(element){
            return element.text().replace(/\"/g, '');
        }, copy(textContent) {
            const input = $("#copy");
            input.val(textContent);
            input.focus();
            input.select();
            document.execCommand("copy");
            $.notify('Data copied.', {
                className: 'alert alert-warning'
            });
        }
    });

    return DocumentsViewer;
});
