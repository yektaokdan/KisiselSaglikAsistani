-- Veritabanını oluştur
CREATE DATABASE IF NOT EXISTS KisiselSaglikDB;
USE KisiselSaglikDB;

-- Kullanıcılar tablosu
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(100) NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Kullanıcı profilleri tablosu
CREATE TABLE UserProfiles (
    ProfileID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    Boy FLOAT,
    Kilo FLOAT,
    Yas INT,
    Cinsiyet VARCHAR(10),
    LastUpdated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Günlük sağlık verileri tablosu
CREATE TABLE HealthData (
    HealthDataID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    SuTuketimi INT,
    UykuSuresi FLOAT,
    AdimSayisi INT,
    RuhHali VARCHAR(20),
    KayitTarihi DATE DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- BMI geçmişi tablosu
CREATE TABLE BMIHistory (
    BMIID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    BMIDegeri FLOAT,
    Kategori VARCHAR(20),
    OlcumTarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- İndeksler
CREATE INDEX IX_Users_Username ON Users(Username);
CREATE INDEX IX_HealthData_UserID_Date ON HealthData(UserID, KayitTarihi);
CREATE INDEX IX_BMIHistory_UserID ON BMIHistory(UserID); 