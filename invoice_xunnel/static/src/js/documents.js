odoo.define('invoice_xunnel.documents', (require) => {

    const DocumentsInspector = require('documents.DocumentsInspector');

    DocumentsInspector.include({
        _renderFields(){
            this._super();
            const only_xunnel = this.records.filter(
                    (record) => record.data.xunnel_attachment);
            if(only_xunnel.length === 1){
                this._renderField('emitter_partner_id', {
                    label: 'Emitter',
                    icon: 'fa fa-user-circle o_documents_folder_color'
                });
                this._renderField('invoice_total_amount', {
                    label: 'Total',
                    icon: 'fa fa-usd o_documents_tag_color'
                });
            }
        }
    })
});
