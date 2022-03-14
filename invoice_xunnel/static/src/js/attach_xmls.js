odoo.define('xunnel_invoice.l10n_mx_edi_vendor_bills_inherit', (require) => {
    'use strict';

    const { attachXmlsWizard } = require('xunnel_invoice.l10n_mx_edi_vendor_bills');

    attachXmlsWizard.include({
        start(){
            this._super.apply(this, arguments);
            if(this.record.context.autofill_enable){
                const names = this.getFilesNames();
                this.autoSelectXML(names);
            }
        }, getFilesNames(){
            let names;
            try{
                names = JSON.parse(this.record.context.file_names);
                if(!names){
                    names = [];
                }
            }catch{
                names = [];
            }
            return names;
        }, autoSelectXML(values){
            const files = [];
            for(let value of values){
                const file = new File([atob(value.text)], value.name, {type: 'text/xml'});
                files.push(file);
            }
            this.handleFileUpload(files);
        }
    });

    return { attachXmlsWizard };
});
