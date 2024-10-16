odoo.define('my_custom_module.custom_payment_screen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.payment_screen');
    const Registries = require('point_of_sale.Registries');

    const CustomPaymentScreen = PaymentScreen => class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            if (this.env.pos.config.cash_rounding) {
                if (!this.env.pos.get_order().check_paymentlines_rounding()) {
                    this._display_popup_error_paymentlines_rounding();
                    return;
                }
            }
            if (await this._isOrderValid(isForceValidate)) {
                // remove pending payments before finalizing the validation
                for (let line of this.paymentLines) {
                    if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                }

                await this._finalizeValidation();

                // Aquí se ejecuta tu método para crear una instancia de gic.payment
                await this.createGicPayment();
            }
        }

        // Método para crear la instancia de gic.payment
        async createGicPayment() {
            const order = this.env.pos.get_order();
            const paymentMethod = this.env.pos.config.payment_method_id;

            try {
                await this.rpc({
                    model: 'gic.payment',
                    method: 'create',
                    args: [{
                        order_date: new Date(),
                        pos_id: this.env.pos.pos_session.id,
                        order_id: order.id,
                        user_id: this.env.pos.get_user().id,
                        payment_method_id: paymentMethod.id,
                        order_amount: order.get_total_with_tax(),
                        cliente_id: order.get_client() ? order.get_client().id : false,
                    }],
                });
                console.log('GIC Payment created successfully');
            } catch (error) {
                console.error('Error creating GIC Payment:', error);
            }
        }
    };

    Registries.Component.extend(PaymentScreen, CustomPaymentScreen);
});
