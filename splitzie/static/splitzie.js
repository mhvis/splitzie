/**
 * Group store using LocalStorage API.
 */
document.addEventListener('alpine:init', () => {

    // Store for the known groups in the browser
    const groupsKey = "groupStore";
    Alpine.store('groups', {
        init() {
            this.groups = JSON.parse(localStorage.getItem(groupsKey) || '{}');
        },
        groups: {},

        /**
         * Adds a group and stores it into LocalStorage.
         *
         * @param {string} code
         * @param {string} name
         */
        add: function (code, name) {
            this.groups[code] = {'name': name};
            localStorage.setItem(groupsKey, JSON.stringify(this.groups));
        },

        /**
         * Removes a group from the store and browser data.
         *
         * @param {string} code
         */
        remove: function (code) {
            delete this.groups[code];
            localStorage.setItem(groupsKey, JSON.stringify(this.groups));
        },
    });
});


class Divider {
    /** @type {number} */
    amount = 0;
    /** @type {Object<id: number, amount: number, division: number>[]} */
    entities;

    /**
     * Initialize the entities.
     *
     * @param {number[]} ids The entity IDs. The order in which it is given
     *   determines who gets the remaining cents.
     */
    constructor(ids) {
        this.entities = ids.map((v) => ({id: v, amount: 0, division: undefined}))
    }

    /**
     * Gets entity by id.
     */
    getEntity(id) {
        for (const e of this.entities) {
            if (e.id === id) {
                return e;
            }
        }
        throw new Error("Invalid id");
    }

    static toEuros(amount) {
        return amount / 100;
    }

    static toCents(amount) {
        return Math.round(amount * 100);
    }

    /**
     * Sets the amount field in cents.
     *
     * @param {number} amount The amount in euros.
     */
    setAmount(amount) {
        this.amount = Divider.toCents(amount);
    }

    /**
     * Sets the amount for an entity.
     *
     * @param {number} id
     * @param {number} amount
     */
    setEntityAmount(id, amount) {
        if (Number.isNaN(amount)) {
            this.getEntity(id).amount = 0;
        } else {
            this.getEntity(id).amount = Divider.toCents(amount);
        }
    }

    /**
     * Sets the division count for an entity.
     *
     * Setting it to undefined makes the entity be treated as a custom value.
     *
     * @param {number} id
     * @param {number|undefined} division
     */
    setEntityDivision(id, division) {
        this.getEntity(id).division = division;
    }

    /**
     * Increments or decrements the entity division number.
     *
     * When the division was undefined, it will be set to 0+delta.
     *
     * @param {number} id
     * @param {number} delta If positive, will increment, else it will decrement.
     */
    incrementDivision(id, delta) {
        const e = this.getEntity(id);
        if (e.division === undefined) {
            e.division = delta;
        } else {
            e.division += delta;
        }
    }

    /**
     * Computes the total amount to divide over the selected entities.
     */
    divideAmount() {
        const customAmountSum = this.entities.reduce(
            (sum, e) => (e.division === undefined ? sum + e.amount : sum),
            0
        );
        return this.amount - customAmountSum;
    }

    /**
     * Computes the number of divisions that need to be done.
     */
    divideCount() {
        return this.entities.reduce(
            (sum, e) => (e.division !== undefined ? sum + e.division : sum),
            0
        );
    }

    /**
     * Computes the calculated division *in cents*.
     *
     * Returns an object with IDs for keys and the amount as value. IDs that
     * have an undefined division are omitted.
     */
    getDivision() {
        const numerator = this.divideAmount();
        const denominator = this.divideCount();
        const quotient = Math.floor(numerator / denominator);
        let remainder = numerator % denominator;

        const division = {};

        for (const e of this.entities) {
            if (e.division === undefined) {
                continue;
            }
            // We add on the remainder until it is exhausted
            const extra = Math.min(remainder, e.division);
            remainder -= extra;

            // Compute the amount, add the remaining, and convert to euros.
            division[e.id] = Divider.toEuros((quotient * e.division) + extra);
        }

        console.log("getDivision", division, this);

        return division;
    }
}
