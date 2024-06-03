({
    name: "MPU6050", // Category Name
    description: "Read gyro data from mpu6050",
    author: "Nawa Phansaen",
    category: "Sensors",
    version: "1.1.0",
    icon: "/static/icon.png", // Category icon
    color: "#E74C3C", // Category color (recommend some blocks color)
    blocks: [ // Blocks in Category
    {
        xml: '<label text="For Setup MPU6050"></label>',
    },
        "mpu6050_Setup",
    {
        xml: '<label text="For read data from mpu6050"></label>',
    },
        "mpu6050_Update",
        "mpu6050_get_Acc",
        "mpu6050_get_Gyro",
        "mpu6050_get_Angle",
    ],
});
