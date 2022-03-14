odoo.define('account_xunnel.add_account_manager', require => {
    "use strict";
    const Action = require('web.AbstractAction');
    const { action_registry, qweb } = require('web.core');
    const AccountManager = Action.extend({
        template: 'account_xunnel.add_account_manager',
        start () {
            const deff = this._super.apply(this, arguments).then(() => {
                return this._rpc({
                    model: 'res.users',
                    method: 'get_xunnel_token',
                }).then(({src, token, locale, css }) => {
                    this.locale = locale;
                    this.token = token;
                    const link = document.createElement('link');
                    const script = document.createElement('script');
                    link.rel = 'stylesheet';
                    link.href = css;
                    script.src = src;
                    script.async = false;
                    script.onload = () => {
                        this.$('.__js_dynamic_content__').html($(qweb.render('account_xunnel.add_account_start_manager')));
                        this.$('.__css_btn_start_manager__').click(ev => {
                            ev.preventDefault();
                            this.openManager();
                        });
                    }
                    window.document.head.append(link);
                    window.document.head.append(script);
                });
            });
            return deff;
        },
        renderButtons ($node) {
            this.$el.parents('.modal').find('header').remove();
            $node.remove();
        },
        openManager () {
            this.$el.parents('.modal').addClass('__css_paybook_widget__').find('.modal-content').addClass('__css_paybook_widget_container__');
            const widget = new SyncWidget({
                token: this.token,
                element: '.__css_paybook_widget_container__',
                config: { locale: moment.locale(), navigation:{ quickAnswer: true } },
            });
            widget.$on('closed', () => window.location.reload());
            widget.$on('status', (...args) => console.warn(...args));
            widget.open();
        }
    });
    action_registry.add('tag.xunnel.add.account.manager', AccountManager);
    return AccountManager;
});
