//
//  Test.swift
//  deserialization_nscoding
//
//  Created by sams on 07/03/2023.
//

import Foundation

class ExampleGadget: NSObject, NSSecureCoding {
    
    public static var supportsSecureCoding = true
    
    let command: String

    internal init(command: String) {
        self.command = command
    }
    
    
    func encode(with coder: NSCoder) {
        coder.encode(command, forKey: "command")
    }
    
    required init?(coder: NSCoder) {
        command = coder.decodeObject(forKey: "command") as! String

        super.init()
        var result = sink1(tainted: command)
        print(result)
    }
    
    
    func sink1(tainted: String) -> String {

            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/bin/bash")
            process.arguments = ["-c", tainted]
            let pipe = Pipe()
            process.standardOutput = pipe
            process.launch()
            process.waitUntilExit()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            guard let output: String = String(data: data, encoding: .utf8) else { return "" }
        return output

}
}
    
    
    
