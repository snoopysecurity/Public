//
//  main.swift
//  deserialization_nscoding
//
//  Created by sams on 07/03/2023.
//

import Foundation

class Employee: NSObject, NSSecureCoding {
    
    public static var supportsSecureCoding = true
    var name: String
    var role: String
    
    init(name: String, role: String) {
        self.name = name
        self.role = role
    }
    
    required convenience init?(coder aDecoder: NSCoder) {
        guard let name = aDecoder.decodeObject(forKey: "name") as? String,
              let role = aDecoder.decodeObject(forKey: "role") as? String else {
            return nil
        }
        
        self.init(name: name, role: role)
    }
    
    func encode(with aCoder: NSCoder) {
        aCoder.encode(name, forKey: "name")
        aCoder.encode(role, forKey: "role")
    }
}

// Archive the Person object to a file
//let person = Employee(name: "John", role: "consultant")
//let fileURL = URL(fileURLWithPath: "/tmp/file")
//NSKeyedArchiver.archiveRootObject(person, toFile: fileURL.path)

if let unarchivedPerson = NSKeyedUnarchiver.unarchiveObject(withFile: "/tmp/file2") as? Employee {
    print("Name: \(unarchivedPerson.name), Role: \(unarchivedPerson.role)")
} else {
    print("Failed to unarchive Employee object")
}



//let gadget = ExampleGadget(command: "ls")
//let fileURL2 = URL(fileURLWithPath: "/tmp/file2")
//NSKeyedArchiver.archiveRootObject(gadget, toFile: fileURL2.path)


// Unarchive the Person object from the file
/*
if let unarchivedPerson = NSKeyedUnarchiver.unarchiveObject(withFile: "/tmp/file2") as? Employee {
    print("Name: \(unarchivedPerson.name), Role: \(unarchivedPerson.role)")
} else {
    print("Failed to unarchive Employee object")
}
*/

let fileURLDecoded = URL(fileURLWithPath: "/tmp/file2")
do {
    let dataDecoded = try Data(contentsOf: fileURLDecoded)
    let unarchiver = try NSKeyedUnarchiver(forReadingFrom: dataDecoded) // This initializer enables requiresSecureCoding by default
    unarchiver.requiresSecureCoding = true
    let decodedDataObject = try unarchiver.decodeTopLevelObject()
    unarchiver.finishDecoding()
    
    let pokeMirror = Mirror(reflecting: decodedDataObject)
    let properties = pokeMirror.children
    for property in properties {
        
        print("\(property.label!) = \(property.value)")
        
    }
}
    
