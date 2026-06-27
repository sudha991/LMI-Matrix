import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import React from "react";

const ExportExcel = ({ data, columns, fileName = "LMI_Report.xlsx" }) => {

  const handleExport = () => {

    if (!data || data.length === 0) {
      alert("No data to export");
      return;
    }

    const exportData = data.map((row, index) => {

      const obj = {
        "S NO": index + 1
      };

      columns.forEach(col => {

        const val = row[col];

        // 🔥 Handle department columns (array)
        if (Array.isArray(val)) {
          obj[col] = val
            .map(v => `${v.clause} (Pg:${v.page})`)
            .join(" | ");
        } else {
          obj[col] = val || "";
        }
      });

      return obj;
    });

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(workbook, worksheet, "LMI Data");

    // ✅ Auto column width
    const colWidths = Object.keys(exportData[0]).map(key => ({
      wch: Math.max(key.length + 5, 20)
    }));
    worksheet["!cols"] = colWidths;

    const excelBuffer = XLSX.write(workbook, {
      bookType: "xlsx",
      type: "array"
    });

    const file = new Blob([excelBuffer], {
      type:
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8"
    });

    saveAs(file, fileName);
  };

  return (
    <button onClick={handleExport} className="btn-export">
      📥 Export Excel
    </button>
  );
};

export default ExportExcel;