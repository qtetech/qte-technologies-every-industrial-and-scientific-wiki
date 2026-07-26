<?php
namespace QteTechnologies\IndustrialScientificCatalog;

class Catalog {
    /**
     * Lấy đường dẫn thư mục gốc của gói nơi chứa các file CSV
     */
    public static function getBaseDir() {
        return dirname(__DIR__);
    }

    /**
     * Tự động quét và lấy danh sách tất cả các file CSV của QTE
     */
    public static function getAllCsvFiles() {
        $baseDir = self::getBaseDir();
        $files = glob($baseDir . '/*.csv');
        return array_map('basename', $files);
    }

    /**
     * Lấy đường dẫn tuyệt đối đến một file dữ liệu cụ thể
     */
    public static function getFilePath($fileName) {
        return self::getBaseDir() . '/' . $fileName;
    }

    /**
     * Đọc nội dung thô của file CSV công nghiệp
     */
    public static function getRawData($fileName) {
        $filePath = self::getFilePath($fileName);
        if (!file_exists($filePath)) {
            throw new \Exception("File {$fileName} không tồn tại trong danh mục dữ liệu QTE.");
        }
        return file_get_contents($filePath);
    }
}
