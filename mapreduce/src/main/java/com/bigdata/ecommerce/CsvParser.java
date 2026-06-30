package com.bigdata.ecommerce;

/**
 * Parses CSV lines from the e-commerce dataset.
 * Format: transaction_id,date,product,category,price,quantity,client_id
 */
public final class CsvParser {

    private CsvParser() {
    }

    public static Transaction parse(String line) {
        if (line == null || line.isEmpty()) {
            return null;
        }
        if (line.startsWith("transaction_id")) {
            return null;
        }

        String[] parts = line.split(",", -1);
        if (parts.length < 7) {
            return null;
        }

        try {
            return new Transaction(
                    parts[0].trim(),
                    parts[1].trim(),
                    parts[2].trim(),
                    parts[3].trim(),
                    Double.parseDouble(parts[4].trim()),
                    Integer.parseInt(parts[5].trim()),
                    parts[6].trim()
            );
        } catch (NumberFormatException e) {
            return null;
        }
    }

    public static class Transaction {
        public final String transactionId;
        public final String date;
        public final String product;
        public final String category;
        public final double price;
        public final int quantity;
        public final String clientId;

        public Transaction(String transactionId, String date, String product,
                           String category, double price, int quantity, String clientId) {
            this.transactionId = transactionId;
            this.date = date;
            this.product = product;
            this.category = category;
            this.price = price;
            this.quantity = quantity;
            this.clientId = clientId;
        }

        public double revenue() {
            return price * quantity;
        }
    }
}
