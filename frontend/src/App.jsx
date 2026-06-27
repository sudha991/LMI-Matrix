import React, { useState, useEffect } from "react";
import axios from "axios";
import Header from "./Header";
import "./style.css";
import ExportExcel from "./components/ExportExcel";
import Login from "./Login";

function App() {

  const API = "http://10.0.180.28:5000";
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("token")
  );
  const [showLogin, setShowLogin] = useState(false);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [selectedRow, setSelectedRow] = useState(null);

  const [data, setData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [columns, setColumns] = useState([]);

  const [search, setSearch] = useState("");
  const [docType, setDocType] = useState("");
  const [custodian, setCustodian] = useState("");
  const [department, setDepartment] = useState("");

  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const [sortConfig, setSortConfig] = useState({ key: "", direction: "asc" });

  const rowsPerPage = 10;
  const handleEdit = (row, col, value) => {
    row[col] = value;   // update UI instantly
    setFilteredData([...filteredData]); // re-render
  };
  const handleSave = (row) => {
    const token = localStorage.getItem("token");

    axios.post(`${API}/update-header`, {
      file_name: row["FILE NAME"],
      revision: row["REVISION"],
      date: row["DATE"],
      custodian: row["CUSTODIAN DEPT"]
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }).then(() => {
      alert("Saved");
      loadData();
    });
  };
    const [editRow, setEditRow] = useState(null);
  const [editData, setEditData] = useState({
    DATE: "",
    REVISION: "",
    "CUSTODIAN DEPT": ""
  });

  const fixedColumns = [
    "FILE NAME",
    "DOC TYPE",
    "TC DOC NO",
    "CUSTODIAN DEPT",
    "REVISION",
    "DATE"
  ];

  // =========================
  // LOAD DATA
  // =========================
  useEffect(() => {
  let dynamicCols = columns.filter(col => !fixedColumns.includes(col));

  let newColumns = [...fixedColumns];

  if (department && dynamicCols.includes(department)) {

    const dateIndex = newColumns.indexOf("DATE");

    newColumns.splice(dateIndex + 1, 0, department);

    dynamicCols = dynamicCols.filter(col => col !== department);
  }

  setColumns([...newColumns, ...dynamicCols]);

}, [department]);
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const res = await axios.get(`${API}/data`);
    const finalData = res.data.data;

    const allCols = new Set();

    finalData.forEach(row => {
      Object.keys(row).forEach(k => {
        if (k !== "S NO") allCols.add(k);
      });
    });

    const dynamicCols = Array.from(allCols).filter(
      col => !fixedColumns.includes(col)
    );

    setColumns([...fixedColumns, ...dynamicCols.sort()]);
    setData(finalData);
    setFilteredData(finalData);
  };

  // =========================
  // FILTER
  // =========================
  useEffect(() => {
    let filtered = [...data];

    if (search) {
      filtered = filtered.filter(row =>
        Object.values(row).some(val =>
          JSON.stringify(val).toLowerCase().includes(search.toLowerCase())
        )
      );
    }

    if (docType) {
      filtered = filtered.filter(row => row["DOC TYPE"] === docType);
    }

    if (custodian) {
      filtered = filtered.filter(row => row["CUSTODIAN DEPT"] === custodian);
    }

    if (department) {
      filtered = filtered.filter(row =>
        Array.isArray(row[department]) && row[department].length > 0
      );
    }

    setFilteredData(filtered);
    setCurrentPage(1);

  }, [search, docType, custodian, department, data]);

  // =========================
  // SORT
  // =========================
  const sortData = (key) => {

    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }

    const sorted = [...filteredData].sort((a, b) => {

      let valA = a[key];
      let valB = b[key];

      if (Array.isArray(valA)) valA = valA.length;
      if (Array.isArray(valB)) valB = valB.length;

      valA = valA ? valA.toString().toLowerCase() : "";
      valB = valB ? valB.toString().toLowerCase() : "";

      if (valA < valB) return direction === "asc" ? -1 : 1;
      if (valA > valB) return direction === "asc" ? 1 : -1;
      return 0;
    });

    setFilteredData(sorted);
    setSortConfig({ key, direction });
  };

  const indexOfLast = currentPage * rowsPerPage;
  const indexOfFirst = indexOfLast - rowsPerPage;
  const currentRows = filteredData.slice(indexOfFirst, indexOfLast);
  const totalPages = Math.ceil(filteredData.length / rowsPerPage);

  const uniqueDocTypes = [...new Set(data.map(d => d["DOC TYPE"]).filter(Boolean))];
  const uniqueCustodians = [...new Set(data.map(d => d["CUSTODIAN DEPT"]).filter(Boolean))];
  const departmentColumns = columns.filter(col => !fixedColumns.includes(col));

  // =========================
  // UI login 
  // =========================
    // =========================
  // SAVE EDIT
  // =========================
  const saveEdit = () => {
    const token = localStorage.getItem("token");

    axios.post(`${API}/update-header`, {
      file_name: editRow["FILE NAME"],
      revision: editData.REVISION,
      date: editData.DATE,
      custodian: editData["CUSTODIAN DEPT"]
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }).then(() => {
      alert("Updated successfully");
      setEditRow(null);
      loadData();
    });
  };
  return (
    <div>
      <Header 
        isLoggedIn={isLoggedIn} 
        setIsLoggedIn={setIsLoggedIn}
        setShowLogin={setShowLogin}
      />

      {/* ✅ LOGIN POPUP ONLY */}
      {showLogin && (
        <div className="login-modal">

          <div 
            className="login-overlay"
            onClick={() => setShowLogin(false)}
          />

          <div className="login-box">
            <Login 
              setIsLoggedIn={setIsLoggedIn} 
              closeModal={() => setShowLogin(false)}
            />
          </div>

        </div>
      )}
      <div style={{ padding: "10px" }}>

        {/* BUTTONS */}
        <button onClick={() => {
          setLoading(true);
          axios.get(`${API}/process`).then(res => {
            alert(`Processed ${res.data.processed}`);
            loadData();
            setLoading(false);
          });
        }}>
          {loading ? "⏳ Processing..." : "🚀 Process PDFs"}
        </button>

        <button onClick={loadData} style={{ marginLeft: "10px" }}>
          🔄 Refresh
        </button>

        {/* FILTERS */}
        <div className="filter-bar-simple">

        <input
          type="text"
          placeholder="🔍 Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />

        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="filter-select"
        >
          <option value="">All Doc Types</option>
          {uniqueDocTypes.map((d, i) => (
            <option key={i}>{d}</option>
          ))}
        </select>

        <select
          value={custodian}
          onChange={(e) => setCustodian(e.target.value)}
          className="filter-select"
        >
          <option value="">All Custodian</option>
          {uniqueCustodians.map((c, i) => (
            <option key={i}>{c}</option>
          ))}
        </select>

        <select
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          className="filter-select"
        >
          <option value="">All Departments</option>
          {departmentColumns.map((dept, i) => (
            <option key={i}>{dept}</option>
          ))}
        </select>

        <button
          className="btn-clear"
          onClick={() => {
            setSearch("");
            setDocType("");
            setCustodian("");
            setDepartment("");
          }}
        >
          Clear
        </button>
        <ExportExcel 
          data={filteredData}   // 🔥 or currentRows if you want page-wise
          columns={columns}
        />
      </div>

        {/* TABLE */}
        <div className="table-container">

          <table className="modern-table">

            <thead>
              <tr>
                <th className="th-sticky first-col">S NO</th>
                <th className="th-sticky first-col">Edit</th>
                {columns.map((col, idx) => (
                  <th
                    key={col}
                    onClick={() => sortData(col)}
                    className={`th-sticky 
                      ${col === department ? "th-highlight" : ""} 
                      ${idx === 0 ? "second-col" : ""}`}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {currentRows.map((row, i) => (
                <tr key={i}>

                  {/* S NO */}
                  <td className="first-col">
                    {indexOfFirst + i + 1}
                  </td>
                   {/* EDIT BUTTON */}
                  <td>
                    {localStorage.getItem("role") === "ADMIN" && (
                      <button onClick={() => {
                        setEditRow(row);
                        setEditData({
                          DATE: row["DATE"] || "",
                          REVISION: row["REVISION"] || "",
                          "CUSTODIAN DEPT": row["CUSTODIAN DEPT"] || ""
                        });
                      }}>
                        ✏
                      </button>
                    )}
                  </td>
                  {columns.map((col, idx) => {

                    const cellValue = row[col];

                    if (Array.isArray(cellValue)) {
                      return (
                        <td
                          key={col}
                          className={`
                            ${col === department ? "td-highlight" : ""}
                            ${idx === 0 ? "second-col" : ""}
                          `}
                        >
                          {cellValue.map((item, idx) => (
                            <div key={idx}>
                              <span
                                className="link"
                                onClick={() => {
                                  setSelectedPdf({
                                    file: item.file,
                                    page: item.page
                                  });
                                  setSelectedRow(row["FILE NAME"]);
                                }}
                              >
                                {item.clause} | {item.page}
                              </span>
                            </div>
                          ))}
                        </td>
                      );
                    }

                    // =====================
                    // TC DOC CLICK
                    // =====================
                    if (col === "TC DOC NO" && cellValue) {
                      return (
                        <td
                          key={col}
                          className={col === department ? "td-highlight" : ""}
                        >
                          <span
                            className="link"
                            onClick={() => {
                              setSelectedPdf({
                                file: row["FILE NAME"],
                                page: 1
                              });
                              setSelectedRow(row["FILE NAME"]);
                            }}
                          >
                            {cellValue}
                          </span>
                        </td>
                      );
                    }

                    const role = localStorage.getItem("role");

                      if (
                        col === "DATE" ||
                        col === "REVISION" ||
                        col === "CUSTODIAN DEPT"
                      ) {
                        return (
                          <td key={col}>
                            {role === "ADMIN" ? (
                              <input
                                value={cellValue || ""}
                                onChange={(e) =>
                                  handleEdit(row, col, e.target.value)
                                }
                              />
                            ) : (
                              cellValue || ""
                            )}
                          </td>
                        );
                      }
                        // 🔥 DEFAULT
                        return <td key={col}>{cellValue || ""}</td>;
                  })}
                  {/* ✅ ADD SAVE BUTTON HERE (ONLY PLACE) */}
                  
                </tr>
              ))}
            </tbody>

          </table>

          

        </div>
{/* PAGINATION */}
         <div className="pagination">

          <button
            onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
            disabled={currentPage === 1}
          >
            ⬅
          </button>

          {[...Array(totalPages)].map((_, i) => {
            const page = i + 1;

            return (
              <button
                key={i}
                onClick={() => setCurrentPage(page)}
                className={currentPage === page ? "active-page" : ""}
              >
                {page}
              </button>
            );
          })}

          <button
            onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
            disabled={currentPage === totalPages}
          >
            ➡
          </button>

        </div>
        {/* MODAL */}
        {selectedPdf && (
          <div className="pdf-modal">

            <div
              className="pdf-overlay"
              onClick={() => setSelectedPdf(null)}
            />

            <div className="pdf-container">

              <div className="pdf-header">
                <span>{selectedPdf.file}</span>
                <button onClick={() => setSelectedPdf(null)}>✖</button>
              </div>

              <iframe
                src={`${API}/pdf/${selectedPdf.file}#page=${selectedPdf.page}`}
                title="PDF"
                width="100%"
                height="100%"
              />

            </div>
          {editRow && (
            <div className="login-modal">

              <div
                className="login-overlay"
                onClick={() => setEditRow(null)}
              />

              <div className="login-box">

                <h3>Edit Header</h3>

                <label>Date</label>
                <input
                  value={editData.DATE}
                  onChange={(e) =>
                    setEditData({ ...editData, DATE: e.target.value })
                  }
                />

                <label>Revision</label>
                <input
                  value={editData.REVISION}
                  onChange={(e) =>
                    setEditData({ ...editData, REVISION: e.target.value })
                  }
                />

                <label>Custodian</label>
                <input
                  value={editData["CUSTODIAN DEPT"]}
                  onChange={(e) =>
                    setEditData({
                      ...editData,
                      "CUSTODIAN DEPT": e.target.value
                    })
                  }
                />

                <div style={{ marginTop: "10px" }}>
                  <button
                    onClick={() => {
                      const token = localStorage.getItem("token");

                      axios.post(`${API}/update-header`, {
                        file_name: editRow["FILE NAME"],
                        revision: editData.REVISION,
                        date: editData.DATE,
                        custodian: editData["CUSTODIAN DEPT"]
                      }, {
                        headers: {
                          Authorization: `Bearer ${token}`
                        }
                      }).then(() => {
                        alert("Updated successfully");
                        setEditRow(null);
                        loadData();
                      });
                    }}
                  >
                    💾 Save
                  </button>

                  <button
                    style={{ marginLeft: "10px" }}
                    onClick={() => setEditRow(null)}
                  >
                    ❌ Cancel
                  </button>
                </div>

              </div>
            </div>
          )}
          </div>
        )}

      </div>
    </div>
  );
}

export default App;