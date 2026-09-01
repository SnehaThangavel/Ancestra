import React from "react";

export function DataTable({ columns, data, emptyMessage = "No records found." }) {
  return (
    <div style={styles.tableWrapper}>
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            {columns.map((col, idx) => (
              <th
                key={idx}
                style={{
                  ...styles.th,
                  textAlign: col.align || "left",
                  width: col.width || "auto"
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={styles.emptyTd}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr key={row.id || rowIdx} style={styles.bodyRow}>
                {columns.map((col, colIdx) => (
                  <td
                    key={colIdx}
                    style={{
                      ...styles.td,
                      textAlign: col.align || "left"
                    }}
                  >
                    {col.render ? col.render(row) : row[col.accessor]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  tableWrapper: {
    width: "100%",
    overflowX: "auto",
    border: "1px solid var(--border-color)",
    borderRadius: "6px",
    backgroundColor: "#FFFFFF"
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "12px",
    fontFamily: "var(--font-sans)"
  },
  headerRow: {
    backgroundColor: "#F7F4EE",
    borderBottom: "1px solid var(--border-color)"
  },
  th: {
    padding: "10px 12px",
    fontSize: "10.5px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: "0.07em",
    color: "#8E857B",
    whiteSpace: "nowrap"
  },
  bodyRow: {
    borderBottom: "1px solid var(--border-light)",
    transition: "background-color 0.1s ease"
  },
  td: {
    padding: "10px 12px",
    color: "var(--text-primary)",
    verticalAlign: "middle"
  },
  emptyTd: {
    padding: "24px",
    textAlign: "center",
    color: "var(--text-muted)",
    fontSize: "12px"
  }
};
