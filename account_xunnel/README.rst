.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Account Xunnel
==============

This app allows you to synchronize your bank statements from Xunnel with Odoo


**How To**
-------------
<details>
<summary>Set Up Your Instance</summary>
- If you don't have any Xunnel Account you must create one at www.xunnel.com.
- Login to your account.
- Sync the accounts or banks that you need in the company.
- Copy the token of the company.
- Go to Accounting > Configuration > Settings > Xunnel Account and paste the token in Xunnel Token field.
.. figure:: account_xunnel/static/description/settings-add-token.png
This can also be done in Accounting > Configuration > Xunnel > Set up token.
.. figure:: account_xunnel/static/description/add-token-menuitme.png
</details>
<details>
<summary>Synchronize Xunnel Accounts</summary>
- Go to Accounting > Configuration > Settings > Xunnel Account and press the button "SYNCHRONIZE BANKS & ACCOUNTS".
This button can also be found in Accounting > Configuration > Accounting > Online Synchronization.
.. figure:: account_xunnel/static/description/sync-accounts-button-accounting.png
If the synchronization was successful you could check those accounts in
Accounting > Configuration > Accounting > Online Synchronization.
.. figure:: account_xunnel/static/description/online-sync-menuitem.png
</details>
<details>
<summary>Link An Account to A Journal</summary>
- To create a new Journal go to **Accounting > Configuration > Accounting > Journals**.
- Click the **Create** button and make sure that your journal has Type as **Bank** and Bank Feeds as **Automated Bank Synchronization**.
- Go to Accounting > Configuration > Accounting > Online Synchronization and select the account you want, in the form
view click the **Edit** button and select the journal you just created to the **Journals** field of any account.
.. figure:: account_xunnel/static/description/link-account-to-journal.png
- Go to Accounting > Dashboard and in your journal click the link **Synchronize now**.
.. figure:: account_xunnel/static/description/sync-now-button.jpg
Those movements could be seen by clicking on the title of your journal.
</details>
<details>
<summary>Add A New Account</summary>
- To create a new Account go to **Accounting > Configuration > Xunnel > Credentials manager**.
- Follow the steps of the widget to add your new account.
- when you finished repeat the process of *Synchronize Accounts* to see your brand new account.
</details>

To check some videos go to [Xunnel User Manual](https://xunnel.com/en_US/user-manual)

**Maintainer**
--------------

.. image:: https://xunnel.com/logo.png
   :alt: Xunnel
   :target: https://www.xunnel.com/

This module is maintained by Xunnel.
