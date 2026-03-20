// swift-tools-version:5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "AgentLinker",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "AgentLinker",
            targets: ["AgentLinker"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/daltoniam/Starscream.git", from: "4.0.0"),
    ],
    targets: [
        .executableTarget(
            name: "AgentLinker",
            dependencies: [
                .product(name: "Starscream", package: "Starscream")
            ],
            path: "Sources",
            resources: [
                .process("Resources")
            ]
        ),
    ]
)
