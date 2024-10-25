/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class ModulaSyncClientAction extends Component {
    setup() {
        this.notification = useService("notification");
        this.action = useService("action");
        this.rpc = useService("rpc");

        const { context } = this.props.action;
        this.model = context.active_model;
        this.res_id = context.active_id;

        this.loadPickingData();
    }

    async loadPickingData() {
        try {
            // Recupera i dati del picking
            const pickings = await this.rpc("/web/dataset/call_kw", {
                model: this.model,
                method: "read",
                args: [[this.res_id], ["id", "name", "picking_type_id", "partner_id", "location_id", "location_dest_id", "scheduled_date", "date_done", "move_ids_without_package"]],
                kwargs: {},
            });

            if (pickings && pickings.length > 0) {
                this.picking = pickings[0];

                // Recupera i dati del picking type
                const pickingTypeId = this.picking.picking_type_id[0];
                const pickingTypes = await this.rpc("/web/dataset/call_kw", {
                    model: "stock.picking.type",
                    method: "read",
                    args: [[pickingTypeId], ["id", "code"]],
                    kwargs: {},
                });

                if (pickingTypes && pickingTypes.length > 0) {
                    this.pickingType = pickingTypes[0];

                    // Recupera i dati delle linee di movimento
                    const moveIds = this.picking.move_ids_without_package;
                    const moves = await this.rpc("/web/dataset/call_kw", {
                        model: "stock.move",
                        method: "read",
                        args: [moveIds, ["id", "location_id", "location_dest_id", "product_id", "product_uom_qty", "quantity"]],
                        kwargs: {},
                    });

                    // Recupera i dati dei prodotti
                    const productIds = moves.map(move => move.product_id[0]);
                    const products = await this.rpc("/web/dataset/call_kw", {
                        model: "product.product",
                        method: "read",
                        args: [productIds, ["id", "default_code", "name"]],
                        kwargs: {},
                    });

                    this.productsMap = products.reduce((acc, product) => {
                        acc[product.id] = product;
                        return acc;
                    }, {});

                    this.moves = moves;

                    // Recupera i dati delle ubicazioni
                    const locationIds = [
                        this.picking.location_id[0], 
                        this.picking.location_dest_id[0],
                        ...moves.map(move => move.location_id[0]),
                        ...moves.map(move => move.location_dest_id[0])
                    ];
                    const uniqueLocationIds = [...new Set(locationIds)];
                    
                    const locations = await this.rpc("/web/dataset/call_kw", {
                        model: "stock.location",
                        method: "read",
                        args: [uniqueLocationIds, ["id", "name"]],
                        kwargs: {},
                    });

                    this.locationsMap = locations.reduce((acc, loc) => {
                        acc[loc.id] = loc.name;
                        return acc;
                    }, {});

                    this.syncModula();
                } else {
                    throw new Error("Unable to retrieve picking type data.");
                }
            } else {
                throw new Error("Unable to retrieve picking data.");
            }
        } catch (error) {
            console.error("Errore durante il caricamento dei dati di picking:", error);
            this.notification.add(`Errore durante il caricamento dei dati di picking: ${error.message}`, {
                type: "danger",
            });
        }
    }

    async syncModula() {
        try {
            const pickingData = this.getPickingData();
            const formData = new FormData();
            const pickingDataString = JSON.stringify(pickingData);
            const blob = new Blob([pickingDataString], { type: "application/json" });
            formData.append("fileUP", blob, "pickingData.json");

            const response = await fetch("http://localhost:5000/apis/modulaupload", {
                method: "POST",
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data && data.status) {
                const result = data.status;
                this.notification.add(result, {
                    type: "success",
                });
                // Imposta modula_sync a True
                await this.rpc("/web/dataset/call_kw", {
                    model: this.model,
                    method: "write",
                    args: [[this.res_id], { modula_sync: true }],
                    kwargs: {},
                });
            } else {
                throw new Error(data);
            }
        } catch (error) {
            console.error("Errore completo:", error);
            this.notification.add(`Errore durante la sincronizzazione: ${error.message}`, {
                type: "danger",
            });
        }
        this.action.doAction({ type: "ir.actions.act_window_close" });
    }

    getPickingData() {
        return {
            picking: this.picking.name,
            scheduled_date: this.picking.scheduled_date,
            effective_date: this.picking.date_done,
            partner: this.picking.partner_id[1],
            operation: this.pickingType.code,
            source: this.locationsMap[this.picking.location_id[0]],
            source_modula: this.locationsMap[this.picking.location_id[0]],
            destination: this.locationsMap[this.picking.location_dest_id[0]],
            destination_modula: this.locationsMap[this.picking.location_dest_id[0]],
            lines: this.moves.map(line => ({
                id: line.id,
                source: this.locationsMap[line.location_id[0]],
                destination: this.locationsMap[line.location_dest_id[0]],
                product_code: this.productsMap[line.product_id[0]].default_code,
                product_name: this.productsMap[line.product_id[0]].name,
                quantity_ordered: line.product_uom_qty,
                quantity_done: line.quantity,
            })),
        };
    }
}

ModulaSyncClientAction.template = "modula_sync.ModulaSyncClientAction";

registry.category("actions").add("modula_sync_action", ModulaSyncClientAction);
