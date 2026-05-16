const path = require('path');
const fs = require('fs');

/**
 * Tự động quét thư mục gốc và lấy danh sách tất cả các file CSV đang có
 * @returns {string[]} Mảng chứa tên các file CSV (VD: ['file1.csv', 'file2.csv'])
 */
const getAllCsvFiles = () => {
    // __dirname đại diện cho thư mục gốc nơi package được cài đặt
    const files = fs.readdirSync(__dirname);
    
    // Lọc và chỉ giữ lại các file có đuôi .csv
    return files.filter(file => path.extname(file).toLowerCase() === '.csv');
};

/**
 * Lấy đường dẫn tuyệt đối của một file cụ thể
 * @param {string} fileName Tên file cần lấy đường dẫn
 */
const getFilePath = (fileName) => {
    return path.join(__dirname, fileName);
};

/**
 * Đọc nội dung thô của một file bất kỳ trong kho
 * @param {string} fileName Tên file cần đọc
 */
const getRawData = (fileName) => {
    const filePath = getFilePath(fileName);
    if (!fs.existsSync(filePath)) {
        throw new Error(`File ${fileName} không tồn tại trong danh mục dữ liệu QTE.`);
    }
    return fs.readFileSync(filePath, 'utf8');
};

module.exports = {
    getAllCsvFiles,
    getFilePath,
    getRawData
};
